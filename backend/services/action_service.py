import random
from dataclasses import dataclass
from enum import Enum


class ActionType(str, Enum):
    GO_TO = "go_to"
    TALK_TO = "talk_to"
    WANDER = "wander"
    IDLE = "idle"
    COMMAND = "command"


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

# Zara: stressed HR boss — paperwork, coffee, bossing people, occasional patrol
# Kron: glued to desk — only leaves for coffee or server emergencies, hates socializing
# Nyx: paranoid patrol — corners, security points, rarely at desk, watches everyone
# Vex: social butterfly — schmoozing, whiteboard "strategy", meetings, never at desk
# Pip: chaos gremlin — bouncing between server racks, fixing things, gossiping, never stops
NPC_ROUTINES: dict[str, list[tuple[str, int]]] = {
    "npc_zara": [
        ("desk_zara", 35), ("coffee_machine", 12), ("water_cooler", 8),
        ("printer", 8), ("meeting_table", 8), ("whiteboard", 6),
        ("command_kron", 8), ("command_pip", 6), ("command_vex", 4), ("command_nyx", 2),
        ("wander", 3),
    ],
    "npc_kron": [
        ("desk_kron", 65), ("coffee_machine", 13), ("server_rack", 12),
        ("printer", 6), ("wander", 4),
    ],
    "npc_nyx": [
        ("desk_nyx", 20), ("whiteboard", 5), ("coffee_machine", 5),
        ("server_rack", 20), ("printer", 5),
        ("wander", 25), ("wander", 20),  # patrol
    ],
    "npc_vex": [
        ("desk_vex", 15), ("meeting_table", 22), ("whiteboard", 16),
        ("coffee_machine", 12), ("talk_to_npc_zara", 8),
        ("talk_to_npc_kron", 8), ("talk_to_npc_pip", 6),
        ("water_cooler", 8), ("wander", 5),
    ],
    "npc_pip": [
        ("desk_pip", 15), ("server_rack", 22), ("coffee_machine", 12),
        ("vending", 12), ("printer", 10),
        ("talk_to_npc_kron", 10), ("talk_to_npc_zara", 6), ("talk_to_npc_vex", 5),
        ("wander", 8),
    ],
}

# Per-NPC activity labels for shared points
NPC_ACTIVITY_LABELS: dict[str, dict[str, str]] = {
    "npc_zara": {
        "desk_zara": "处理离职文件...",
        "coffee_machine": "续命咖啡...第四杯了",
        "water_cooler": "接水顺便观察谁在摸鱼...",
        "printer": "打印解雇通知书...",
        "meeting_table": "开裁员会议...",
        "whiteboard": "更新组织架构图...",
        "wander": "巡视办公室...",
    },
    "npc_kron": {
        "desk_kron": "修 Bug...72小时没睡了",
        "coffee_machine": "紧急补充咖啡因...",
        "server_rack": "重启服务器...又崩了",
        "printer": "打印堆栈日志...",
        "wander": "去找更多咖啡...",
    },
    "npc_nyx": {
        "desk_nyx": "审查安全日志...",
        "coffee_machine": "观察咖啡机监控数据...",
        "server_rack": "检查入侵痕迹...",
        "printer": "打印加密报告...",
        "whiteboard": "更新威胁评估...",
        "wander": "安全巡逻...",
    },
    "npc_vex": {
        "desk_vex": "优化个人品牌定位...",
        "coffee_machine": "在咖啡机旁'偶遇'同事...",
        "meeting_table": "开颠覆性策略会...",
        "whiteboard": "画增长曲线...全是右上",
        "water_cooler": "在饮水机旁social...",
        "wander": "寻找'协同机会'...",
    },
    "npc_pip": {
        "desk_pip": "拆装无人机零件...",
        "coffee_machine": "给咖啡机加'性能增强模块'...",
        "server_rack": "偷偷加补丁...Kron还没发现",
        "vending": "补充零食储备...",
        "printer": "修卡纸...第18次了",
        "water_cooler": "换饮水机滤芯...反正没人换",
        "wander": "到处溜达找八卦...",
    },
}

# Fallback generic labels
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

    def _npc_label(self, npc_id: str, point_id: str, fallback: str = "") -> str:
        """Get character-specific activity label, fall back to generic."""
        return NPC_ACTIVITY_LABELS.get(npc_id, {}).get(point_id, fallback or DIALOGUE_TAGS.get(point_id, ""))

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
        actions_map: dict[str, NPCAction] = {}
        self._point_occupants = {}

        for npc_id in all_npc_ids:
            action = self._pick_action(npc_id)
            actions_map[npc_id] = action
            self._current_actions[npc_id] = action

        # --- Supervisor: Zara commands override subordinate actions ---
        zara = actions_map.get("npc_zara")
        if zara and zara.action_type == ActionType.COMMAND.value:
            target_id = zara.target_id
            if target_id in actions_map:
                desk = INTEREST_POINTS.get("desk_zara", {"position": (320, 600)})
                # Extract subordinate response from packed dialogue
                sub_response = "Zara叫我去一趟..."
                if "||" in zara.dialogue_line:
                    _, sub_response = zara.dialogue_line.split("||", 1)
                actions_map[target_id] = NPCAction(
                    npc_id=target_id,
                    action_type=ActionType.GO_TO.value,
                    target_id="desk_zara",
                    target_position=self._jitter(desk["position"], target_id, 30),
                    dialogue_line=sub_response,
                    duration=8.0,
                )

        # Serialize
        actions = []
        for npc_id in all_npc_ids:
            a = actions_map[npc_id]
            tid = a.target_id
            if tid and tid not in ("wander", ""):
                if tid not in self._point_occupants:
                    self._point_occupants[tid] = []
                self._point_occupants[tid].append(npc_id)
            dl = a.dialogue_line
            if a.action_type == ActionType.COMMAND.value and "||" in dl:
                dl = dl.split("||")[0]  # Zara's line only in serialized output
            actions.append({
                "npc_id": a.npc_id,
                "action_type": a.action_type,
                "target_id": a.target_id,
                "target_position": list(a.target_position),
                "dialogue_line": dl,
                "duration": a.duration,
            })
        return actions

    def _pick_action(self, npc_id: str) -> NPCAction:
        routines = NPC_ROUTINES.get(npc_id, [("wander", 100)])
        # Context-aware stickiness: stay longer at desk, cycle faster from elsewhere
        keep_chance = 0.8 if (npc_id in self._current_actions and self._current_actions[npc_id].target_id.startswith("desk_")) else 0.2
        if npc_id in self._current_actions and random.random() < keep_chance:
            return self._current_actions[npc_id]
        available = [(t, w) for t, w in routines if not self._is_point_crowded(t)]
        if not available:
            available = routines
        choices, weights = zip(*available)
        picked = random.choices(choices, weights=weights, k=1)[0]

        # --- COMMAND: Zara bosses someone around ---
        if picked.startswith("command_"):
            target_npc = "npc_" + picked.split("_", 1)[1]
            target_name = {
                "npc_kron": "Kron", "npc_pip": "Pip", "npc_vex": "Vex", "npc_nyx": "Nyx"
            }.get(target_npc, target_npc)
            cmds = [
                ("去把报告给我整理好，现在。", "……知道了。马上。"),
                ("你，到我办公室来一趟。", "好的好的我来了！"),
                ("别摸鱼了，服务器又有异常。去看。", "行行行这就去……"),
                ("那份文件你今天必须交。", "今天？！……好，我加班。"),
            ]
            zara_line, sub_line = random.choice(cmds)
            return NPCAction(
                npc_id=npc_id,
                action_type=ActionType.COMMAND.value,
                target_id=target_npc,
                target_position=(320, 600),
                dialogue_line=zara_line + "||" + sub_line,  # both lines packed
                duration=6.0,
            )

        # --- talk_to_player ---
        if picked == "talk_to_player":
            return NPCAction(
                npc_id=npc_id,
                action_type="talk_to_player",
                target_id="player",
                target_position=(0, 0),
                dialogue_line="来找你聊聊...",
                duration=12.0,
            )

        # --- talk_to_* ---
        if picked.startswith("talk_to_"):
            target_short = picked.replace("talk_to_npc_", "")
            talk_point = INTEREST_POINTS.get("desk_" + target_short)
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
                target_position=(random.uniform(100, 1100), random.uniform(150, 650)),
                dialogue_line=self._npc_label(npc_id, "wander", "随便走走..."),
                duration=random.uniform(3.0, 7.0),
            )

        # --- desk ---
        if picked.startswith("desk_"):
            point = INTEREST_POINTS.get(picked)
            target_pos = self._jitter(point["position"], npc_id, 10) if point else (640, 360)
            return NPCAction(
                npc_id=npc_id,
                action_type=ActionType.IDLE.value,
                target_id=picked,
                target_position=target_pos,
                dialogue_line=self._npc_label(npc_id, picked, "工位上办公..."),
                duration=random.uniform(20.0, 40.0),
            )

        # --- shared interest point ---
        point = INTEREST_POINTS.get(picked)
        target_pos = self._jitter(point["position"], npc_id, 22) if point else (500, 360)
        is_quick = picked in ("coffee_machine", "water_cooler", "vending")
        dur = random.uniform(3.0, 7.0) if is_quick else random.uniform(5.0, 12.0)
        return NPCAction(
            npc_id=npc_id,
            action_type=ActionType.GO_TO.value,
            target_id=picked,
            target_position=target_pos,
            dialogue_line=self._npc_label(npc_id, picked, "Interacting..."),
            duration=dur,
        )
