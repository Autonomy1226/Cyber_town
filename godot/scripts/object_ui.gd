extends CanvasLayer

var _current_object_id: String = ""
var _actions: Array = []
var _money: int = 0

@onready var _panel: Panel = $Panel
@onready var _name_label: Label = $Panel/VBoxContainer/ObjectName
@onready var _action_list: ItemList = $Panel/VBoxContainer/ActionList
@onready var _result_label: Label = $Panel/VBoxContainer/ResultLabel
@onready var _close_btn: Button = $Panel/VBoxContainer/CloseBtn

func _ready():
	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0.06, 0.06, 0.1, 0.93)
	bg.set_corner_radius_all(10)
	_panel.add_theme_stylebox_override("panel", bg)
	_action_list.item_selected.connect(_on_action_selected)
	_close_btn.pressed.connect(hide)

func open(object_id: String):
	_current_object_id = object_id
	_result_label.text = ""

	# Get player money
	ApiClient.fetch_player(Globals.player_id, func(data, err):
		if not err:
			_money = data.get("money", 0)
	)

	ApiClient.fetch_objects(func(data, err):
		if err:
			return
		for obj in data.get("objects", []):
			if obj["object_id"] == object_id:
				_name_label.text = obj["name"]
				_actions = obj["actions"]
				_action_list.clear()
				for act in _actions:
					var label = act["label"]
					_action_list.add_item(label)
				visible = true
				return
	)

func _on_action_selected(idx: int):
	if idx < 0 or idx >= _actions.size():
		return
	var action = _actions[idx]["action"]
	ApiClient.interact_object(_current_object_id, action, func(data, err):
		if err:
			_result_label.text = "[网络错误]"
			return
		var txt = data.get("result", "")
		var item = data.get("item_gained", "")
		var money = data.get("money_current", -1)
		if item:
			txt += "\n\n» 获得: " + item
		if money >= 0:
			_money = money
			txt += "\n» 余额: $" + str(money)
		_result_label.text = txt
	)

func _input(event: InputEvent):
	if event.is_action_pressed("ui_cancel") and visible:
		hide()
