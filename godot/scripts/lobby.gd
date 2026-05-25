extends Node2D

const TILE_SIZE: int = 32
const W: int = 30
const H: int = 20

func _ready():
	var world_w = W * TILE_SIZE
	var world_h = H * TILE_SIZE
	var wall = 16.0
	var door_x = 640.0
	var door_w = 80.0

	# Floor
	for x in range(W):
		for y in range(H):
			$GroundLayer.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))

	# Walls with door gap at bottom
	var edges = [
		{ "pos": Vector2(world_w / 2, -wall / 2), "size": Vector2(world_w, wall) },  # top
		{ "pos": Vector2(-wall / 2, world_h / 2), "size": Vector2(wall, world_h) },    # left
		{ "pos": Vector2(world_w + wall / 2, world_h / 2), "size": Vector2(wall, world_h) },  # right
		# bottom-left segment
		{ "pos": Vector2((door_x - door_w / 2) / 2, world_h), "size": Vector2(door_x - door_w / 2, wall) },
		# bottom-right segment
		{ "pos": Vector2(door_x + door_w / 2 + (world_w - door_x - door_w / 2) / 2, world_h), "size": Vector2(world_w - door_x - door_w / 2, wall) },
	]
	for edge in edges:
		var body = StaticBody2D.new()
		body.collision_layer = 1
		var col = CollisionShape2D.new()
		var rect = RectangleShape2D.new()
		rect.size = edge["size"]
		col.shape = rect
		body.add_child(col)
		body.position = edge["pos"]
		add_child(body)

	# Door in the wall gap
	var door = Node2D.new()
	door.position = Vector2(door_x, world_h)
	door.name = "DoorBack"
	add_child(door)

	var zone = Area2D.new()
	zone.name = "Trigger"
	zone.add_to_group("doors")
	zone.set_meta("target_scene", "res://scenes/main.tscn")
	zone.set_meta("spawn_marker", "from_lobby")
	var shape = CollisionShape2D.new()
	var rect = RectangleShape2D.new()
	rect.size = Vector2(door_w, 14)
	shape.shape = rect
	zone.add_child(shape)
	door.add_child(zone)

	var label = Label.new()
	label.text = "» 办公室"
	label.position = Vector2(0, -16)
	label.add_theme_font_size_override("font_size", 11)
	label.add_theme_color_override("font_color", Color(0.3, 0.9, 1, 0.8))
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	door.add_child(label)

	# Spawn player
	var player_scene = load("res://scenes/player.tscn")
	var player = player_scene.instantiate()
	var sp = $SpawnPoints.get_node_or_null("from_office")
	player.position = sp.position if sp else Vector2(640, 360)
	Globals.spawn_marker = ""
	add_child(player)

	# Spawn UIs
	var dialogue = load("res://scenes/dialogue_ui.tscn").instantiate()
	dialogue.name = "DialogueUI"
	dialogue.visible = false
	add_child(dialogue)
	var inv = load("res://scenes/inventory_ui.tscn").instantiate()
	inv.name = "InventoryUI"
	add_child(inv)
	var obj = load("res://scenes/object_ui.tscn").instantiate()
	obj.name = "ObjectUI"
	add_child(obj)
	var iu = load("res://scenes/inspect_ui.tscn").instantiate()
	iu.name = "InspectUI"
	add_child(iu)
	var cl = load("res://scenes/chatlog_ui.tscn").instantiate()
	cl.name = "ChatLogUI"
	add_child(cl)
