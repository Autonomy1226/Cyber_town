extends CanvasLayer

var _items: Array = []
var _money: int = 0

@onready var _panel: Panel = $Panel
@onready var _money_label: Label = $Panel/VBoxContainer/TitleBar/MoneyLabel
@onready var _item_list: ItemList = $Panel/VBoxContainer/ItemList
@onready var _desc_label: Label = $Panel/VBoxContainer/DescLabel

func _ready():
	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0.06, 0.06, 0.1, 0.93)
	bg.set_corner_radius_all(10)
	bg.content_margin_left = 10
	bg.content_margin_right = 10
	_panel.add_theme_stylebox_override("panel", bg)
	_item_list.item_selected.connect(_on_item_selected)

func _input(event: InputEvent):
	if not event.is_action_pressed("inventory"):
		return
	if event.is_action_pressed("ui_cancel") and visible:
		hide()
		return
	var dialogue = get_node("../DialogueUI")
	var obj_ui = get_node("../ObjectUI")
	if (dialogue and dialogue.visible) or (obj_ui and obj_ui.visible):
		return
	if visible:
		hide()
	else:
		_refresh()

func _refresh():
	ApiClient.fetch_player(Globals.player_id, func(data, err):
		if err:
			return
		_items = data.get("items", [])
		_money = data.get("money", 0)
		_money_label.text = "$" + str(_money)
		_item_list.clear()
		for item in _items:
			var label = item["name"]
			if item["type"] == "consumable":
				label += " [可使用]"
			_item_list.add_item(label)
		_desc_label.text = "共 %d 件物品  余额 $%d" % [_items.size(), _money]
		visible = true
	)

func _on_item_selected(idx: int):
	if idx < 0 or idx >= _items.size():
		return
	var item = _items[idx]
	_desc_label.text = "%s\n%s\n类型: %s  价值: $%d" % [item["name"], item["desc"], item["type"], item["value"]]
