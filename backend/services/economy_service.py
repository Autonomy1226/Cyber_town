import random
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Item:
    item_id: str
    name: str
    desc: str
    item_type: str  # consumable / key / junk / tool
    value: int = 0  # sell/buy price


ITEM_DB: dict[str, Item] = {
    "energy_drink":  Item("energy_drink",  "能量饮料",   "霓虹绿的提神饮料，标签已经褪色了",  "consumable", 5),
    "coffee_coupon": Item("coffee_coupon", "咖啡兑换券",  "NexCorp 食堂的免费咖啡券，有效期：已过期", "consumable", 3),
    "encrypted_usb": Item("encrypted_usb", "加密U盘",    "贴着'机密——仅限CSO'标签的U盘",    "key", 20),
    "old_circuit":   Item("old_circuit",   "旧电路板",   "从服务器上拆下来的废弃电路板",      "junk", 2),
    "data_shard":    Item("data_shard",    "数据碎片",   "一片损坏的存储芯片，或许还能读取",   "junk", 8),
    "id_badge":      Item("id_badge",      "员工ID卡",   "一张模糊的NexCorp员工卡，名字已看不清", "key", 15),
    "hack_tool":     Item("hack_tool",     "黑客工具",   "Pip 自制的万能接口，能打开大多数终端", "tool", 25),
    "sake_flask":    Item("sake_flask",    "清酒壶",     "Zara 藏在抽屉里的清酒，还剩半壶",   "consumable", 10),
    "neural_patch":  Item("neural_patch",  "神经补丁",   "Kron 一直没装的固件更新补丁",       "junk", 5),
    "marketing_report": Item("marketing_report", "营销报告", "Vex 的 Q4 营销计划，充满了'颠覆性'和'赋能'", "junk", 3),
}


class PlayerEconomy:
    """Per-player inventory + money (in-memory, resets on backend restart)."""

    def __init__(self):
        self.money: int = 50
        self.inventory: list[str] = []

    def add_item(self, item_id: str) -> bool:
        if item_id not in ITEM_DB:
            return False
        self.inventory.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.inventory:
            self.inventory.remove(item_id)
            return True
        return False

    def has_item(self, item_id: str) -> bool:
        return item_id in self.inventory

    def add_money(self, amount: int):
        self.money += amount

    def spend_money(self, amount: int) -> bool:
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def get_inventory(self) -> list[dict]:
        return [
            {"item_id": iid, "name": ITEM_DB[iid].name, "desc": ITEM_DB[iid].desc,
             "type": ITEM_DB[iid].item_type, "value": ITEM_DB[iid].value}
            for iid in self.inventory
        ]


class EconomyService:
    def __init__(self):
        self._players: dict[str, PlayerEconomy] = {}

    def get_player(self, player_id: str) -> PlayerEconomy:
        if player_id not in self._players:
            self._players[player_id] = PlayerEconomy()
        return self._players[player_id]


# --- Object interaction logic ---

INTERACTABLE_OBJECTS = {
    "coffee_machine": {
        "name": "咖啡机",
        "actions": [
            {"action": "drink", "label": "喝杯咖啡 (免费)", "result": "你按了下按钮，一杯温热的黑咖啡流了出来。苦涩但提神。"},
            {"action": "inspect", "label": "检查咖啡机", "result": "咖啡机侧面贴着一张褪色的便条：'最后一次维护：三个月前。滤网可能堵了。——Pip'"},
        ],
    },
    "vending": {
        "name": "自动售货机",
        "actions": [
            {"action": "buy_drink", "label": "买能量饮料 ($5)", "cost": 5, "item": "energy_drink",
             "result": "售货机哔了一声，掉出一罐冰镇能量饮料。"},
            {"action": "buy_snack", "label": "买零食 ($3)", "cost": 3, "item": "coffee_coupon",
             "result": "一包可疑的零食掉了出来。包装上写着'最佳食用日期：去年'。"},
            {"action": "kick", "label": "踹一脚", "result": "你踹了售货机一脚。它晃了一下，发出不满的嗡嗡声。什么都没掉出来。"},
        ],
    },
    "printer": {
        "name": "打印机",
        "actions": [
            {"action": "print", "label": "打印一份测试页", "result": "打印机嘎吱作响，吐出一张全是乱码的纸。纸的背面有人手写了：'谁拿了我的订书机？？——Zara'",
             "item": "marketing_report"},
            {"action": "inspect", "label": "检查打印队列", "result": "屏幕上显示最后一份打印任务来自'Vex Holloway'，标题：'颠覆性Q4品牌策略——机密'。已卡纸。"},
        ],
    },
    "server_rack": {
        "name": "服务器机柜",
        "actions": [
            {"action": "search", "label": "翻找零件", "result": "你在机柜底部的缝隙里找到了一块被遗弃的电路板。",
             "item": "old_circuit"},
            {"action": "hack", "label": "尝试黑客工具连接", "result": "你用黑客工具接入了服务器……发现 Pip 已经在上面打了补丁。顺便在日志里找到一片数据碎片。",
             "item": "data_shard", "require_item": "hack_tool"},
            {"action": "inspect", "label": "检查服务器状态", "result": "指示灯疯狂闪烁。有人（大概率 Kron）在跑一个死循环进程。CPU 占用 99%。"},
        ],
    },
    "whiteboard": {
        "name": "白板",
        "actions": [
            {"action": "read", "label": "看白板内容", "result": "白板上画满了流程图和潦草的字。'Nyx: 安保审计 Q3 → Kron: 修支付系统 → Vex: ？？？' 旁边有人画了一只愤怒的猫。"},
            {"action": "draw", "label": "画个笑脸", "result": "你在白板角落画了个笑脸。好像多了点什么……也许其他 NPC 会注意到。"},
        ],
    },
    "water_cooler": {
        "name": "饮水机",
        "actions": [
            {"action": "drink", "label": "接杯水 (免费)", "result": "你接了一杯水。温的。NexCorp 连饮水机都没钱修了。"},
            {"action": "gossip", "label": "在饮水机旁偷听", "result": "你靠在饮水机旁假装喝水……这里确实是茶水间八卦的中心。你听到了一些关于 Nyx 的安保审计的碎碎念。"},
        ],
    },
}


def interact_object(player_id: str, object_id: str, action: str, economy: EconomyService) -> dict:
    """Handle object interaction. Returns result dict with optional item/money changes."""
    obj = INTERACTABLE_OBJECTS.get(object_id)
    if not obj:
        return {"error": f"未知物品: {object_id}"}

    player = economy.get_player(player_id)
    act = None
    for a in obj["actions"]:
        if a["action"] == action:
            act = a
            break
    if not act:
        return {"error": f"无效操作: {action}"}

    req_item = act.get("require_item")
    if req_item and not player.has_item(req_item):
        return {"result": f"需要 {ITEM_DB.get(req_item, Item(req_item, req_item, '', '')).name} 才能执行此操作。", "error_detail": "missing_item"}

    cost = act.get("cost", 0)
    if cost > 0 and not player.spend_money(cost):
        return {"result": f"余额不足！需要 ${cost}。", "error_detail": "insufficient_funds"}

    item_id = act.get("item")
    if item_id:
        player.add_item(item_id)

    result = {
        "result": act["result"],
        "money_change": -cost if cost > 0 else 0,
        "money_current": player.money,
        "item_gained": ITEM_DB[item_id].name if item_id and item_id in ITEM_DB else None,
    }
    return result
