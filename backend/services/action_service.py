import random
from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    GO_TO = "go_to"
    TALK_TO = "talk_to"
    WANDER = "wander"
    IDLE = "idle"


@dataclass
class NPCAction:
    npc_id: str
    action_type: str
    target_id: str
    target_position: tuple[float, float]
    dialogue_line: str
    duration: float


INTEREST_POINTS: dict[str, dict] = {
    "desk_zara":    {"name": "Zara's Desk",      "position": (320, 600)},
    "desk_kron":    {"name": "Kron's Desk",      "position": (640, 400)},
    "desk_nyx":     {"name": "Nyx's Office",     "position": (960, 250)},
    "desk_vex":     {"name": "Vex's Office",     "position": (160, 350)},
    "desk_pip":     {"name": "Pip's IT Corner",  "position": (800, 650)},
    "coffee_machine":{"name": "Coffee Machine",   "position": (500, 200)},
    "water_cooler": {"name": "Water Cooler",     "position": (500, 550)},
    "printer":      {"name": "Printer",           "position": (700, 200)},
    "meeting_table":{"name": "Meeting Table",     "position": (500, 300)},
    "server_rack":  {"name": "Server Rack",       "position": (1050, 600)},
    "whiteboard":   {"name": "Whiteboard",        "position": (200, 200)},
    "vending":      {"name": "Vending Machine",   "position": (150, 600)},
}

# Per-NPC: (target_point, weight)  — higher weight = more likely
NPC_ROUTINES: dict[str, list[tuple[str, int]]] = {
    "npc_zara": [
        ("desk_zara", 20), ("coffee_machine", 15), ("water_cooler", 15),
        ("printer", 10), ("meeting_table", 10), ("whiteboard", 10),
        ("vending", 5), ("talk_to_npc_pip", 8), ("talk_to_player", 3), ("wander", 4),
    ],
    "npc_kron": [
        ("desk_kron", 35), ("coffee_machine", 20), ("server_rack", 15),
        ("printer", 10), ("meeting_table", 5), ("talk_to_npc_pip", 10),
        ("talk_to_player", 2), ("wander", 3),
    ],
    "npc_nyx": [
        ("desk_nyx", 25), ("whiteboard", 15), ("coffee_machine", 10),
        ("server_rack", 15), ("meeting_table", 5),
        ("talk_to_npc_zara", 10), ("talk_to_player", 5), ("wander", 15),
    ],
    "npc_vex": [
        ("desk_vex", 20), ("meeting_table", 20), ("whiteboard", 15),
        ("coffee_machine", 12), ("talk_to_npc_zara", 10),
        ("talk_to_npc_kron", 10), ("talk_to_player", 5), ("water_cooler", 3), ("wander", 5),
    ],
    "npc_pip": [
        ("desk_pip", 12), ("server_rack", 22), ("coffee_machine", 15),
        ("vending", 12), ("water_cooler", 8), ("talk_to_npc_kron", 12),
        ("talk_to_npc_vex", 8), ("talk_to_npc_zara", 5), ("talk_to_player", 3), ("wander", 3),
    ],
}

DIALOGUE_TAGS: dict[str, str] = {
    "coffee_machine": "泡咖啡中...",
    "water_cooler": "接水中...",
    "printer": "打印文件...",
    "meeting_table": "开会中...",
    "server_rack": "检查服务器...",
    "whiteboard": "看白板...",
    "vending": "买零食...",
    "wander": "随便走走...",
}

# Per-NPC personal offset from shared points
NPC_OFFSET: dict[str, tuple[float, float]] = {
    "npc_zara": (-20, -15),
    "npc_kron": (20, -10),
    "npc_nyx": (-15, 20),
    "npc_vex": (25, 15),
    "npc_pip": (-25, 10),
}


class ActionService:
    def __init__(self):
        self._current_actions: dict[str, NPCAction] = {}
        self._point_occupants: dict[str, list[str]] = {}

    def _jitter(self, base: tuple[float, float], npc_id: str, amount: float = 18.0) -> tuple[float, float]:
        off = NPC_OFFSET.get(npc_id, (0, 0))
        return (
            base[0] + off[0] + random.uniform(-amount, amount),
            base[1] + off[1] + random.uniform(-amount, amount),
        )

    def _is_point_crowded(self, point_id: str) -> bool:
        return len(self._point_occupants.get(point_id, [])) >= 2

    def get_all_actions(self) -> list[dict]:
        all_npc_ids = list(NPC_ROUTINES.keys())
        actions = []

        # Reset occupancy tracking
        self._point_occupants = {}

        for npc_id in all_npc_ids:
            action = self._pick_action(npc_id)
            self._current_actions[npc_id] = action

            # Track occupancy
            tid = action.target_id
            if tid and tid not in ("wander", ""):
                if tid not in self._point_occupants:
                    self._point_occupants[tid] = []
                self._point_occupants[tid].append(npc_id)

            actions.append({
                "npc_id": action.npc_id,
                "action_type": action.action_type,
                "target_id": action.target_id,
                "target_position": list(action.target_position),
                "dialogue_line": action.dialogue_line,
                "duration": action.duration,
            })

        return actions

    def _pick_action(self, npc_id: str) -> NPCAction:
        routines = NPC_ROUTINES.get(npc_id, [("wander", 100)])

        # 60% chance to keep current action (reduced from 70% for more dynamism)
        if npc_id in self._current_actions and random.random() < 0.6:
            return self._current_actions[npc_id]

        # Filter out crowded points
        available = [(t, w) for t, w in routines if not self._is_point_crowded(t)]
        if not available:
            available = routines

        choices, weights = zip(*available)
        picked = random.choices(choices, weights=weights, k=1)[0]

        # --- talk_to_player — go talk to the player ---
        if picked == "talk_to_player":
            return NPCAction(
                npc_id=npc_id,
                action_type="talk_to_player",
                target_id="player",
                target_position=(0, 0),
                dialogue_line="来找你聊聊...",
                duration=12.0,
            )

        # --- talk_to_* — go chat with another NPC ---
        if picked.startswith("talk_to_"):
            target_short = picked.replace("talk_to_npc_", "")
            talk_point = INTEREST_POINTS.get(f"desk_{target_short}")
            if talk_point:
                target_pos = self._jitter(talk_point["position"], npc_id, 30)
            else:
                target_pos = (random.uniform(300, 900), random.uniform(200, 600))
            return NPCAction(
                npc_id=npc_id,
                action_type=ActionType.TALK_TO.value,
                target_id=picked,
                target_position=target_pos,
                dialogue_line="去找人聊天...",
                duration=random.uniform(4.0, 8.0),
            )

        # --- wander ---
        if picked == "wander":
            return NPCAction(
                npc_id=npc_id,
                action_type=ActionType.WANDER.value,
                target_id="wander",
                target_position=(
                    random.uniform(100, 1100),
                    random.uniform(150, 650),
                ),
                dialogue_line=DIALOGUE_TAGS["wander"],
                duration=random.uniform(3.0, 7.0),
            )

        # --- desk ---
        if picked.startswith("desk_"):
            point = INTEREST_POINTS.get(picked)
            if point:
                target_pos = self._jitter(point["position"], npc_id, 10)
            else:
                target_pos = (640, 360)
            return NPCAction(
                npc_id=npc_id,
                action_type=ActionType.IDLE.value,
                target_id=picked,
                target_position=target_pos,
                dialogue_line="工位上办公...",
                duration=random.uniform(6.0, 15.0),
            )

        # --- shared interest point ---
        point = INTEREST_POINTS.get(picked)
        if point:
            target_pos = self._jitter(point["position"], npc_id, 22)
        else:
            target_pos = (500, 360)
        dialogue = DIALOGUE_TAGS.get(picked, "Interacting...")
        return NPCAction(
            npc_id=npc_id,
            action_type=ActionType.GO_TO.value,
            target_id=picked,
            target_position=target_pos,
            dialogue_line=dialogue,
            duration=random.uniform(4.0, 10.0),
        )
