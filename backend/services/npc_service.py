import logging
import sqlite3
from pathlib import Path
from helloagents import SimpleAgent, NPCProfile, ShortTermMemory, MemoryManager, Message
from helloagents import InMemoryLongTermMemory, QdrantLongTermMemory
from helloagents import FavorabilitySystem
from backend.npcs.personalities import NPC_PERSONALITIES, NPC_POSITIONS

logger = logging.getLogger("cybertown.npc")


class NPCService:
    def __init__(self, llm_client, use_qdrant: bool = False, qdrant_url: str = "", data_dir: str = "backend/data"):
        self._llm_client = llm_client
        self._agents: dict[str, SimpleAgent] = {}
        self._favorability: dict[tuple[str, str], FavorabilitySystem] = {}
        self._db_path = str(Path(data_dir) / "cybertown.db")
        self._loaded_players: set = set()

        self._init_db()
        self._load_favorability()

        for profile in NPC_PERSONALITIES:
            stm = ShortTermMemory(max_size=20)
            if use_qdrant:
                ltm = QdrantLongTermMemory(qdrant_url, f"npc_{profile.npc_id}")
            else:
                ltm = InMemoryLongTermMemory()
            mm = MemoryManager(stm, ltm, llm_client, short_term_window=10)
            fav = FavorabilitySystem(initial=profile.favorability)
            agent = SimpleAgent(profile, mm, fav, llm_client)
            self._agents[profile.npc_id] = agent
            logger.info("Created agent: %s (%s)", profile.name, profile.npc_id)

    # --- Database ---
    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS favorability (
                player_id TEXT NOT NULL,
                npc_id TEXT NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (player_id, npc_id)
            )
        """)
        conn.commit()
        conn.close()

    def _load_favorability(self):
        conn = sqlite3.connect(self._db_path)
        rows = conn.execute("SELECT player_id, npc_id, score FROM favorability").fetchall()
        conn.close()
        count = 0
        for player_id, npc_id, score in rows:
            key = (npc_id, player_id)
            self._favorability[key] = FavorabilitySystem(initial=score)
            self._loaded_players.add(player_id)
            count += 1
        if count:
            logger.info("Loaded %d favorability records from DB", count)

    def _save_favorability(self, player_id: str, npc_id: str, score: int):
        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT OR REPLACE INTO favorability (player_id, npc_id, score) VALUES (?, ?, ?)",
            (player_id, npc_id, score),
        )
        conn.commit()
        conn.close()

    # --- Player history preload ---
    def preload_memory(self, npc_id: str, player_id: str):
        """Load recent chat history into the NPC's short-term memory so they remember past sessions."""
        agent = self.get_agent(npc_id)
        # Only preload if memory is empty (first chat this session)
        if agent.memory._short.get_all():
            return

        conn = sqlite3.connect(self._db_path)
        # Check if chat_history table exists
        table_check = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'"
        ).fetchone()
        if not table_check:
            conn.close()
            return

        rows = conn.execute(
            "SELECT role, text FROM chat_history WHERE player_id = ? AND npc_id = ? ORDER BY id ASC LIMIT 10",
            (player_id, npc_id),
        ).fetchall()
        conn.close()

        for role, text in rows:
            agent.memory._short.add(Message(role=role, content=text))
        if rows:
            logger.info("Preloaded %d history messages for %s/%s", len(rows), player_id, npc_id)

    # --- Public API ---
    def get_agent(self, npc_id: str) -> SimpleAgent:
        if npc_id not in self._agents:
            raise KeyError(f"NPC '{npc_id}' not found")
        return self._agents[npc_id]

    def get_favorability(self, npc_id: str, player_id: str) -> FavorabilitySystem:
        key = (npc_id, player_id)
        if key not in self._favorability:
            default_fav = self._agents[npc_id].profile.favorability if npc_id in self._agents else 0
            self._favorability[key] = FavorabilitySystem(initial=default_fav)
        return self._favorability[key]

    def save_favorability(self, player_id: str, npc_id: str):
        fav = self.get_favorability(npc_id, player_id)
        self._save_favorability(player_id, npc_id, fav.score)

    def list_npcs(self) -> list[dict]:
        result = []
        for prof in NPC_PERSONALITIES:
            result.append({
                "npc_id": prof.npc_id,
                "name": prof.name,
                "role": prof.role,
                "position": NPC_POSITIONS.get(prof.npc_id, (0.0, 0.0)),
            })
        return result

    def get_npc_info(self, npc_id: str, player_id: str) -> dict:
        agent = self.get_agent(npc_id)
        fav = self.get_favorability(npc_id, player_id)
        pos = NPC_POSITIONS.get(npc_id, (0.0, 0.0))
        return {
            "npc_id": agent.profile.npc_id,
            "name": agent.profile.name,
            "role": agent.profile.role,
            "position": pos,
            "current_favorability": fav.score,
        }
