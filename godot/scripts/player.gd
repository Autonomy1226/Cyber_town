extends CharacterBody2D

const SPEED: float = 200.0

var _nearby_npc_areas: Array = []
var _nearby_objects: Array = []
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
	if _is_in_dialogue:
		return

	if event.is_action_pressed("interact"):
		_talk_to_npc()
	elif event.is_action_pressed("inspect"):
		_inspect_npc()
	elif event.is_action_pressed("interact_object"):
		_use_object()

func _talk_to_npc():
	# Accept NPC invite
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

	# Talk to nearest NPC
	var nearest = _get_nearest(_nearby_npc_areas)
	if nearest:
		var npc = nearest.get_parent()
		if npc is CyberNPC:
			_is_in_dialogue = true
			if Globals.dialogue_ui:
				Globals.dialogue_ui.open_dialogue(npc.npc_id, _on_dialogue_closed)

func _inspect_npc():
	var nearest = _get_nearest(_nearby_npc_areas)
	if nearest:
		var npc = nearest.get_parent()
		if npc is CyberNPC:
			var iu = get_node("../InspectUI")
			if iu:
				iu.show_npc(npc.npc_id)

func _use_object():
	var nearest = _get_nearest(_nearby_objects)
	if nearest:
		var object_id = nearest.get_meta("object_id", "")
		if object_id:
			_is_in_dialogue = true
			var obj_ui = get_node("../ObjectUI")
			if obj_ui:
				obj_ui.visible = true
				obj_ui.open(object_id)
			await get_tree().create_timer(0.1).timeout
			_is_in_dialogue = false

func _get_nearest(list: Array) -> Node2D:
	var best = null
	var best_dist = 80.0
	for item in list:
		if not is_instance_valid(item):
			continue
		var dist = global_position.distance_to(item.global_position)
		if dist < best_dist:
			best = item
			best_dist = dist
	return best

func _on_dialogue_closed():
	_is_in_dialogue = false

func _on_area_entered(area: Area2D):
	if area.get_parent() is CyberNPC:
		_nearby_npc_areas.append(area)
	if area.is_in_group("interactable"):
		_nearby_objects.append(area)
	if area.is_in_group("doors"):
		var target = area.get_meta("target_scene", "")
		var spawn = area.get_meta("spawn_marker", "default")
		if target:
			call_deferred("_do_scene_switch", target, spawn)

func _do_scene_switch(target: String, spawn: String):
	SceneManager.go_to(target, spawn)

func _on_area_exited(area: Area2D):
	_nearby_npc_areas.erase(area)
	_nearby_objects.erase(area)
