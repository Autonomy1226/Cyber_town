extends CanvasLayer

@onready var _money_label: Label = $MoneyPanel/MoneyLabel
@onready var _hint_label: Label = $HintPanel/HintLabel

var _player = null

func _ready():
	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0.06, 0.06, 0.1, 0.85)
	bg.set_corner_radius_all(6)
	$MoneyPanel.add_theme_stylebox_override("panel", bg)
	$HintPanel.add_theme_stylebox_override("panel", bg)

func _process(_delta: float):
	if _player == null:
		_player = get_node("../Player")
		if _player == null:
			return

	var npc_nearby = false
	var obj_nearby = false
	for area in _player._nearby_npc_areas:
		if is_instance_valid(area):
			npc_nearby = true
			break
	for area in _player._nearby_objects:
		if is_instance_valid(area):
			obj_nearby = true
			break

	var hints = []
	if npc_nearby:
		hints.append("[E] 对话")
	if obj_nearby:
		hints.append("[F] 互动")
	hints.append("[I] 背包")
	_hint_label.text = "  ".join(hints)

func update_money(amount: int):
	_money_label.text = "$" + str(amount)
