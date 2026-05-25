extends Node2D

const POLL_INTERVAL: float = 10.0
const CHAT_COOLDOWN: float = 30.0
const CHAT_RANGE: float = 75.0
const INVITE_RANGE: float = 100.0
const INVITE_TIMEOUT: float = 12.0

var _npc_nodes: Array = []
var _timer: float = 1.0
var _initialized: bool = false
var _npc_container: Node2D
var _player: CharacterBody2D
var _chat_cooldowns: Dictionary = {}
var _chat_pending: Dictionary = {}
var _invite_timer: float = 0.0
var _prox_timer: float = 0.0
var _seeker_timer: float = 0.0

func _ready():
	_npc_container = get_node("../NPCs")
	_player = get_node("../Player")
	call_deferred("_scan_npcs")

func _scan_npcs():
	_npc_nodes.clear()
	for child in _npc_container.get_children():
		if child is CyberNPC:
			_npc_nodes.append(child)
	Globals.npc_list = _npc_nodes.duplicate()
	_initialized = true
	ApiClient.fetch_npc_actions(_on_actions_received)

func _process(delta: float):
	_timer -= delta
	if _timer <= 0:
		_timer = POLL_INTERVAL
		ApiClient.fetch_npc_actions(_on_actions_received)
	_dispatch_next_action()

	_seeker_timer -= delta
	if _seeker_timer <= 0:
		_seeker_timer = 0.5
		_update_player_seekers(0.5)

	_prox_timer -= delta
	if _prox_timer <= 0:
		_prox_timer = 0.5
		_check_npc_proximity(0.5)

	_check_invite_timeout(delta)

var _pending_actions: Array = []
var _dispatch_idx: int = 0

func _on_actions_received(data, error: bool):
	if error:
		return
	_pending_actions = data.get("actions", [])
	_dispatch_idx = 0

func _dispatch_next_action():
	"""Apply one action per frame to avoid pathfinding spike."""
	if _dispatch_idx >= _pending_actions.size():
		return
	var action = _pending_actions[_dispatch_idx]
	_dispatch_idx += 1
	var npc_id = action.get("npc_id", "")
	var node = _find_npc(npc_id)
	if node:
		var atype = action.get("action_type", "")
		if atype == "talk_to_player":
			var pos_list = [_player.global_position.x, _player.global_position.y]
			action["target_position"] = pos_list
		elif atype == "command":
			node.say(action.get("dialogue_line", ""), 5.0)
		node.do_action(action)

func _find_npc(npc_id: String) -> CyberNPC:
	for npc in _npc_nodes:
		if npc.npc_id == npc_id:
			return npc
	return null

func _update_player_seekers(delta: float):
	for npc in _npc_nodes:
		if npc.current_action.get("action_type") != "talk_to_player":
			continue
		var dist = npc.global_position.distance_to(_player.global_position)
		if npc.current_state == CyberNPC.State.INVITING:
			if dist > INVITE_RANGE + 40:
				npc.set_state(CyberNPC.State.MOVING)
				npc._nav_agent.target_position = _player.global_position
				npc._speech_bubble.visible = false
				npc._show_activity("找你呢别跑...")
			continue
		if npc.current_state == CyberNPC.State.MOVING:
			npc._nav_agent.target_position = _player.global_position
			if dist < INVITE_RANGE and Globals.inviting_npc == null:
				npc.set_state(CyberNPC.State.INVITING)
				npc._show_activity("想跟你聊聊...")
				npc.say("嘿！有空聊两句吗？[E] 接受", 99.0)
				Globals.inviting_npc = npc
				_invite_timer = INVITE_TIMEOUT

func _check_invite_timeout(delta: float):
	if Globals.inviting_npc == null:
		return
	_invite_timer -= delta
	if _invite_timer <= 0:
		_decline_invite()

func _decline_invite():
	if Globals.inviting_npc == null:
		return
	var npc = Globals.inviting_npc
	Globals.inviting_npc = null
	npc.say("算了，下次吧。", 3.0)
	npc.set_state(CyberNPC.State.IDLE)
	npc._show_activity("")
	ApiClient.fetch_npc_actions(func(data, err):
		if not err:
			var actions = data.get("actions", [])
			for a in actions:
				if a.get("npc_id") == npc.npc_id:
					npc.do_action(a)
					return
	)

func _pair_key(a: String, b: String) -> String:
	return a + "_" + b if a < b else b + "_" + a

func _can_chat(id_a: String, id_b: String) -> bool:
	var key = _pair_key(id_a, id_b)
	if _chat_pending.get(key, false):
		return false
	var now = Time.get_ticks_msec() / 1000.0
	var last = _chat_cooldowns.get(key, 0.0)
	if now - last < CHAT_COOLDOWN:
		return false
	_chat_cooldowns[key] = now
	_chat_pending[key] = true
	return true

func _check_npc_proximity(_delta: float):
	for i in range(_npc_nodes.size()):
		for j in range(i + 1, _npc_nodes.size()):
			var a = _npc_nodes[i]
			var b = _npc_nodes[j]
			if a.is_chatting or b.is_chatting:
				continue
			var dist = a.global_position.distance_to(b.global_position)
			if dist < CHAT_RANGE:
				if _can_chat(a.npc_id, b.npc_id):
					_trigger_npc_chat(a, b)

func _trigger_npc_chat(a: CyberNPC, b: CyberNPC):
	if a.current_state != CyberNPC.State.IDLE:
		a.set_state(CyberNPC.State.IDLE)
	if b.current_state != CyberNPC.State.IDLE:
		b.set_state(CyberNPC.State.IDLE)
	var key = _pair_key(a.npc_id, b.npc_id)
	ApiClient.fetch_npc_chat(a.npc_id, b.npc_id, func(data, error):
		_chat_pending[key] = false
		if error:
			return
		var line_a = data.get("npc_a_line", "")
		var line_b = data.get("npc_b_line", "")
		if line_a:
			a.say(line_a, 5.0)
		if line_b:
			b.say(line_b, 5.0)
	)
