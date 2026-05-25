extends Node
# Autoload singleton: wraps HTTPRequest for all backend calls.
# Each request creates its own HTTPRequest node to allow concurrent calls.

func send_chat(npc_id: String, message: String, callback: Callable, ctx = null) -> void:
	var body = {
		"player_id": Globals.player_id,
		"npc_id": npc_id,
		"message": message,
	}
	if ctx != null:
		body["context"] = ctx
	var req = _make_request(callback)
	var url = Globals.backend_url + "/api/chat"
	var headers = ["Content-Type: application/json"]
	req.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(body))

func fetch_npcs(callback: Callable) -> void:
	var req = _make_request(callback)
	req.request(Globals.backend_url + "/api/npc")

func fetch_npc_info(npc_id: String, callback: Callable) -> void:
	var req = _make_request(callback)
	req.request(Globals.backend_url + "/api/npc/%s?player_id=%s" % [npc_id, Globals.player_id])

func fetch_npc_actions(callback: Callable) -> void:
	var req = _make_request(callback)
	req.request(Globals.backend_url + "/api/npc/actions")

func fetch_npc_chat(npc_a: String, npc_b: String, callback: Callable) -> void:
	var body = {"npc_id_a": npc_a, "npc_id_b": npc_b}
	var req = _make_request(callback)
	var url = Globals.backend_url + "/api/npc/npc-chat"
	var headers = ["Content-Type: application/json"]
	req.request(url, headers, HTTPClient.METHOD_POST, JSON.stringify(body))

func fetch_logs(npc_id: String, limit: int, callback: Callable) -> void:
	var url = Globals.backend_url + "/api/logs?limit=%d" % limit
	if npc_id != "":
		url += "&npc_id=" + npc_id
	var req = _make_request(callback)
	req.request(url)

func _make_request(callback: Callable) -> HTTPRequest:
	var req = HTTPRequest.new()
	add_child(req)
	req.request_completed.connect(_on_done.bind(callback, req), CONNECT_ONE_SHOT)
	return req

func _on_done(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray, callback: Callable, req: HTTPRequest):
	if result != HTTPRequest.RESULT_SUCCESS or response_code >= 400:
		callback.call({}, true)
	else:
		var text = body.get_string_from_utf8()
		var json = JSON.new()
		if json.parse(text) == OK:
			callback.call(json.data, false)
		else:
			callback.call({}, true)
	req.queue_free()
