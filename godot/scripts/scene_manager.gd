extends Node
# Autoload — manages scene transitions manually

var _loading_screen_scene = preload("res://scenes/loading_screen.tscn")
var _last_switch_time: float = 0.0

func go_to(target_scene: String, spawn_marker: String = "default"):
	var now = Time.get_ticks_msec() / 1000.0
	if now - _last_switch_time < 2.0:
		return
	_last_switch_time = now

	Globals.spawn_marker = spawn_marker
	Globals.inviting_npc = null
	Globals.dialogue_ui = null
	ApiClient.cancel_all()

	var root = get_tree().root

	# Show loading screen
	var loading = _loading_screen_scene.instantiate()
	loading.name = "LoadingScreen"
	root.add_child(loading)

	# Find and remove current world (first Node2D that is a scene root)
	var old_world = null
	for child in root.get_children():
		if child is Node2D and child != loading and child.scene_file_path != "":
			old_world = child
			break

	if old_world:
		root.remove_child(old_world)
		old_world.queue_free()

	# Load new scene
	var packed = load(target_scene)
	if not packed:
		if is_instance_valid(loading):
			loading.queue_free()
		return

	var new_scene = packed.instantiate()
	root.add_child(new_scene)
	root.move_child(new_scene, 0)

	# Wait for scene to initialize
	await get_tree().process_frame
	await get_tree().process_frame

	# Dismiss loading
	if is_instance_valid(loading):
		loading.finish()
