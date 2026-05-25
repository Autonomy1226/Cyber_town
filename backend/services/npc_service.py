import logging
from helloagents import SimpleAgent, NPCProfile, ShortTermMemory, MemoryManager
from helloagents import InMemoryLongTermMemory, QdrantLongTermMemory
from helloagents import FavorabilitySystem
from backend.npcs.personalities import NPC_PERSONALITIES, NPC_POSITIONS

logger = logging.getLogger("cybertown.npc")


class NPCService:
    def __init__(self, llm_client, use_qdrant: bool = False, qdrant_url: str = ""):
        self._llm_client = llm_client
        self._agents: dict[str, SimpleAgent] = {}
        self._favorability: dict[tuple[str, str], FavorabilitySystem] = {}

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
