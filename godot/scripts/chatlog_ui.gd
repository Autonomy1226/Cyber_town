extends CanvasLayer

@onready var _log_list: RichTextLabel = $Panel/VBox/LogList

func _ready():
	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0.06, 0.06, 0.1, 0.90)
	bg.set_corner_radius_all(10)
	$Panel.add_theme_stylebox_override("panel", bg)

func _input(event: InputEvent):
	if visible and event.is_action_pressed("ui_cancel"):
		hide()
		return
	if event.is_action_pressed("chat_log"):
		if visible:
			hide()
		elif not Globals.dialogue_ui or not Globals.dialogue_ui.visible:
			_refresh()

func _refresh():
	var req = HTTPRequest.new()
	add_child(req)
	req.request_completed.connect(_on_log_loaded.bind(req), CONNECT_ONE_SHOT)
	req.request(Globals.backend_url + "/api/npc/chat-log")

func _on_log_loaded(_r, _c, _h, body, req):
	req.queue_free()
	var json = JSON.new()
	if json.parse(body.get_string_from_utf8()) != OK:
		return
	var entries = json.data.get("entries", [])
	_log_list.clear()
	for e in entries:
		var src = "" if e.get("source", "") == "cache" else " [AI]"
		_log_list.append_text("[color=#888888]---[/color]\n")
		_log_list.append_text("[color=#ffaa66]%s:[/color] %s\n" % [e["npc_a"], e["line_a"]])
		_log_list.append_text("[color=#88ddff]%s:[/color] %s\n" % [e["npc_b"], e["line_b"]])
	visible = true
