extends CharacterBody2D

const SPEED: float = 200.0
const INTERACT_DISTANCE: float = 80.0

var _nearby_npc_areas: Array = []
var _is_in_dialogue: bool = false

@onready var _sprite: Sprite2D = $Sprite2D
@onready var _interact_area: Area2D = $InteractArea

func _ready():
	collision_layer = 2
	collision_mask = 3
	_interact_area.area_entered.connect(_on_area_entered)
	_interact_area.area_exited.connect(_on_area_exited)

func _physics_process(_delta: float):
	if _is_in_dialogue:
		return
	var input_dir = Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = input_dir * SPEED
	move_and_slide()

func _input(event: InputEvent):
	if event.is_action_pressed("interact") and not _is_in_dialogue:
		_try_interact()

func _try_interact():
	# If an NPC is inviting us, accept the invite
	if Globals.inviting_npc and is_instance_valid(Globals.inviting_npc):
		var npc = Globals.inviting_npc
		Globals.inviting_npc = null
		npc.say("", 0.0)
		npc._speech_bubble.visible = false
		npc.set_state(CyberNPC.State.IDLE)
		npc._show_activity("")
		_is_in_dialogue = true
		if Globals.dialogue_ui:
			Globals.dialogue_ui.open_dialogue(npc.npc_id, _on_dialogue_closed)
			Globals.dialogue_ui.trigger_greeting()
		return

	# Filter to areas that still have a valid CyberNPC parent
	var valid_areas: Array = []
	for area in _nearby_npc_areas:
		if is_instance_valid(area) and area.get_parent() is CyberNPC:
			valid_areas.append(area)
	_nearby_npc_areas = valid_areas

	if _nearby_npc_areas.is_empty():
		return

	var closest = _nearby_npc_areas[0]
	var closest_dist = global_position.distance_to(closest.global_position)
	for area in _nearby_npc_areas:
		var dist = global_position.distance_to(area.global_position)
		if dist < closest_dist:
			closest = area
			closest_dist = dist

	if closest_dist <= INTERACT_DISTANCE:
		_is_in_dialogue = true
		var npc = closest.get_parent() as CyberNPC
		if Globals.dialogue_ui:
			Globals.dialogue_ui.open_dialogue(npc.npc_id, _on_dialogue_closed)

func _on_dialogue_closed():
	_is_in_dialogue = false

func _on_area_entered(area: Area2D):
	if area.is_in_group("npc"):
		_nearby_npc_areas.append(area)

func _on_area_exited(area: Area2D):
	_nearby_npc_areas.erase(area)
