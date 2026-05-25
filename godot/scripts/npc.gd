extends CharacterBody2D
class_name CyberNPC

enum State { IDLE, MOVING, INTERACTING, INVITING }

@export var npc_id: String = ""
@export var npc_name: String = "???"
@export var npc_role: String = ""
@export var move_speed: float = 80.0
@export var arrival_threshold: float = 24.0

var current_state: State = State.IDLE
var current_action: Dictionary = {}

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _name_label: Label = $NameLabel
@onready var _activity_label: Label = $ActivityLabel
@onready var _speech_bubble: Label = $SpeechBubble
@onready var _nav_agent: NavigationAgent2D = $NavigationAgent2D
@onready var _interact_area: Area2D = $InteractArea

var _speech_timer: float = 0.0
var is_chatting: bool = false
var _stuck_timer: float = 0.0
var _last_pos: Vector2 = Vector2.ZERO

func _ready():
	collision_layer = 2
	collision_mask = 3
	motion_mode = MOTION_MODE_FLOATING
	add_to_group("npc")
	_name_label.text = npc_name
	_nav_agent.velocity_computed.connect(_on_velocity_computed)
	_last_pos = global_position

	var bubble_bg = StyleBoxFlat.new()
	bubble_bg.bg_color = Color(0.05, 0.05, 0.08, 0.88)
	bubble_bg.set_corner_radius_all(6)
	bubble_bg.content_margin_left = 8
	bubble_bg.content_margin_right = 8
	bubble_bg.content_margin_top = 4
	bubble_bg.content_margin_bottom = 4
	_speech_bubble.add_theme_stylebox_override("normal", bubble_bg)

func _process(delta: float):
	z_index = int(global_position.y)
	if _speech_timer > 0:
		_speech_timer -= delta
		if _speech_timer <= 0:
			_speech_bubble.visible = false
			is_chatting = false
			_show_activity(current_action.get("dialogue_line", ""))

func do_action(action: Dictionary):
	current_action = action
	var action_type = action.get("action_type", "idle")
	var target_id = action.get("target_id", "")
	var target_pos = action.get("target_position", [position.x, position.y])
	var dialogue = action.get("dialogue_line", "")

	if action_type == "talk_to":
		_show_activity("找人聊天...")
	else:
		_show_activity(dialogue)

	if action_type == "idle":
		set_state(State.IDLE)
	elif action_type in ["go_to", "wander", "talk_to", "talk_to_player", "command"]:
		set_state(State.MOVING)
		_nav_agent.target_position = Vector2(target_pos[0], target_pos[1])

func say(text: String, duration: float = 5.0):
	_speech_bubble.text = text
	_speech_bubble.visible = true
	_activity_label.visible = false
	_speech_timer = duration
	is_chatting = true

func _physics_process(delta: float):
	var vel = Vector2.ZERO

	if current_state == State.MOVING:
		var next_pos = _nav_agent.get_next_path_position()
		vel = (next_pos - global_position).normalized() * move_speed
		var dist = global_position.distance_to(_nav_agent.target_position)
		if dist < arrival_threshold:
			set_state(State.INTERACTING)
			_spread_out()

	velocity = vel
	move_and_slide()

func _on_velocity_computed(safe_velocity: Vector2):
	velocity = safe_velocity
	move_and_slide()

func _spread_out():
	# Use cached list from behavior controller (avoids scene tree query every call)
	var others = Globals.npc_list if Globals.npc_list else []
	var push = Vector2.ZERO
	for other in others:
		if other == self or not is_instance_valid(other):
			continue
		var d = global_position.distance_to(other.global_position)
		if d < 32.0 and d > 0.1:
			push += (global_position - other.global_position).normalized() * (32.0 - d)
	if push.length() > 0.5:
		global_position += push * 0.2

func set_state(new_state: State):
	current_state = new_state
	if new_state == State.IDLE:
		velocity = Vector2.ZERO

func _show_activity(text: String):
	if text.is_empty():
		_activity_label.visible = false
		return
	_activity_label.text = text
	_activity_label.visible = true

func get_info() -> Dictionary:
	return {
		"npc_id": npc_id,
		"name": npc_name,
		"role": npc_role,
		"position": [position.x, position.y],
		"state": current_state,
		"action": current_action.get("dialogue_line", ""),
	}
