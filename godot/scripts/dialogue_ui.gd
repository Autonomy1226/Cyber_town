extends CanvasLayer

signal dialogue_closed

func _ready():
	Globals.dialogue_ui = self
	_send_btn.pressed.connect(_on_send_pressed)
	_close_btn.pressed.connect(_on_close_pressed)
	_input_line.text_submitted.connect(_on_text_submitted)

	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0.08, 0.08, 0.12, 0.92)
	bg.set_corner_radius_all(8)
	bg.content_margin_left = 12
	bg.content_margin_right = 12
	bg.content_margin_top = 8
	bg.content_margin_bottom = 8
	_panel.add_theme_stylebox_override("panel", bg)

var _current_npc_id: String = ""
var _message_history: Array = []
var _npc_histories: Dictionary = {}
var _npc_names: Dictionary = {}

@onready var _panel: Panel = $Panel
@onready var _npc_name_label: Label = $Panel/VBoxContainer/Header/NPCName
@onready var _history_rich: RichTextLabel = $Panel/VBoxContainer/Body/HistoryText
@onready var _input_line: LineEdit = $Panel/VBoxContainer/Footer/InputLine
@onready var _send_btn: Button = $Panel/VBoxContainer/Footer/SendBtn
@onready var _close_btn: Button = $Panel/VBoxContainer/Header/CloseBtn
@onready var _fav_bar: ProgressBar = $Panel/VBoxContainer/Header/FavorabilityBar
@onready var _fav_label: Label = $Panel/VBoxContainer/Header/FavorabilityLabel

func open_dialogue(npc_id: String, on_close: Callable):
	_current_npc_id = npc_id

	# Restore or create history for this NPC
	if _npc_histories.has(npc_id):
		_message_history = _npc_histories[npc_id]
	else:
		_message_history = []
		_npc_histories[npc_id] = _message_history

	visible = true
	_history_rich.clear()

	# Rebuild visible history
	if _message_history.is_empty():
		_history_rich.append_text("[color=#888888]--- %s ---[/color]\n\n" % npc_id)
	else:
		for msg in _message_history:
			var role = msg["role"]
			var text = msg["text"]
			var color = "#88ddff" if role == "player" else ("#ffaa66" if role == "npc" else "#aaaaaa")
			var prefix = "[你]" if role == "player" else ("[%s]" % _npc_name_label.text if role == "npc" else "[SYS]")
			_history_rich.append_text("[color=%s]%s[/color] %s\n\n" % [color, prefix, text])

	ApiClient.fetch_npc_info(npc_id, _on_npc_info)

	if _npc_names.has(npc_id):
		_npc_name_label.text = _npc_names[npc_id]

	if dialogue_closed.get_connections().size() > 0:
		dialogue_closed.disconnect(dialogue_closed.get_connections()[0]["callable"])
	dialogue_closed.connect(on_close, CONNECT_ONE_SHOT)

	_input_line.grab_focus()

func trigger_greeting():
	"""Called when NPC initiated conversation. NPC speaks first."""
	_input_line.editable = false
	_append_message("system", "（%s 主动走过来跟你说话）" % _npc_name_label.text)
	ApiClient.send_chat(_current_npc_id, "", _on_chat_response, "npc_greeting")

func _on_npc_info(data: Dictionary, error: bool):
	if error:
		return
	var name = data.get("name", "???")
	_npc_name_label.text = name
	_npc_names[_current_npc_id] = name
	var fav = data.get("current_favorability", 0)
	_update_favorability_display(fav)

func _on_send_pressed():
	_send_message()

func _on_text_submitted(_text: String):
	_send_message()

func _send_message():
	var text = _input_line.text.strip_edges()
	if text.is_empty():
		return
	_input_line.clear()
	_input_line.editable = false

	_append_message("player", text)
	ApiClient.send_chat(_current_npc_id, text, _on_chat_response)

func _on_chat_response(result: Dictionary, error: bool):
	_input_line.editable = true
	_input_line.grab_focus()

	if error:
		_append_message("system", "[无法连接服务器]")
		return

	var reply = result.get("reply", "...")
	_append_message("npc", reply)

	var fav_current = result.get("favorability_current", 0)
	var fav_change = result.get("favorability_change", 0)
	_update_favorability_display(fav_current)

	if fav_change != 0:
		_fav_label.text = "FAV: %d (%+d)" % [fav_current, fav_change]
	else:
		_fav_label.text = "FAV: %d" % fav_current

func _append_message(role: String, text: String):
	_message_history.append({"role": role, "text": text})
	var color = "#88ddff" if role == "player" else ("#ffaa66" if role == "npc" else "#aaaaaa")
	var prefix = "[You]" if role == "player" else ("[%s]" % _npc_name_label.text if role == "npc" else "[SYS]")
	_history_rich.append_text("[color=%s]%s[/color] %s\n\n" % [color, prefix, text])

func _update_favorability_display(score: int):
	var normalized = (score + 100.0) / 200.0 * 100.0
	_fav_bar.value = normalized

	if score <= -61:
		_fav_bar.modulate = Color.RED
	elif score <= -21:
		_fav_bar.modulate = Color.ORANGE_RED
	elif score <= 20:
		_fav_bar.modulate = Color.YELLOW
	elif score <= 60:
		_fav_bar.modulate = Color.GREEN_YELLOW
	else:
		_fav_bar.modulate = Color.GREEN

func _on_close_pressed():
	visible = false
	dialogue_closed.emit()

func _input(event: InputEvent):
	if event.is_action_pressed("ui_cancel") and visible:
		_on_close_pressed()
