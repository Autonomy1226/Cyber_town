extends Node2D

const TILE_SIZE: int = 32
const WORLD_W: int = 40
const WORLD_H: int = 23
const NPC_SPEED: float = 80.0

var _npc_scene: PackedScene = preload("res://scenes/npc.tscn")

var _npc_defs = [
	{ "id": "npc_zara", "name": "Zara Chen", "role": "Head of HR",
	  "pos": Vector2(320, 600), "tex": "res://assets/sprites/npc_zara.png" },
	{ "id": "npc_kron", "name": "Kron-42", "role": "Sr. Software Architect",
	  "pos": Vector2(640, 400), "tex": "res://assets/sprites/npc_kron.png" },
	{ "id": "npc_nyx", "name": "Nyx Vasquez", "role": "Chief Security Officer",
	  "pos": Vector2(960, 250), "tex": "res://assets/sprites/npc_nyx.png" },
	{ "id": "npc_vex", "name": "Vex Holloway", "role": "VP of Marketing",
	  "pos": Vector2(160, 350), "tex": "res://assets/sprites/npc_vex.png" },
	{ "id": "npc_pip", "name": "Pip", "role": "IT Support Specialist",
	  "pos": Vector2(800, 650), "tex": "res://assets/sprites/npc_pip.png" },
]

@onready var _ground_layer: TileMapLayer = $GroundLayer
@onready var _player: CharacterBody2D = $Player
@onready var _dialogue_ui = $DialogueUI
@onready var _nav_region: NavigationRegion2D = $NavigationRegion2D
@onready var _interest_points: Node2D = $InterestPoints
@onready var _npc_container: Node2D = $NPCs

func _ready():
	if _dialogue_ui:
		_dialogue_ui.visible = false
		_dialogue_ui.process_mode = Node.PROCESS_MODE_ALWAYS

	_generate_floor()
	_setup_navigation()
	_spawn_interest_points()
	_spawn_npcs()

	ApiClient.fetch_npcs(_on_npc_list_received)

func _generate_floor():
	for x in range(WORLD_W):
		for y in range(WORLD_H):
			_ground_layer.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))

func _setup_navigation():
	var nav_poly = NavigationPolygon.new()
	var world_rect = PackedVector2Array([
		Vector2(0, 0),
		Vector2(WORLD_W * TILE_SIZE, 0),
		Vector2(WORLD_W * TILE_SIZE, WORLD_H * TILE_SIZE),
		Vector2(0, WORLD_H * TILE_SIZE),
	])
	nav_poly.add_outline(world_rect)
	nav_poly.make_polygons_from_outlines()
	_nav_region.navigation_polygon = nav_poly

func _spawn_interest_points():
	var points = [
		{ "name": "Coffee Machine", "pos": Vector2(500, 200), "tex": "res://assets/sprites/tiles/plant.png", "size": Vector2(24, 24) },
		{ "name": "Water Cooler",   "pos": Vector2(500, 550), "tex": "res://assets/sprites/tiles/plant.png", "size": Vector2(24, 24) },
		{ "name": "Printer",        "pos": Vector2(700, 200), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(48, 24) },
		{ "name": "Meeting Table",  "pos": Vector2(500, 300), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(80, 40) },
		{ "name": "Server Rack",    "pos": Vector2(1050, 600), "tex": "res://assets/sprites/tiles/server_rack.png", "size": Vector2(28, 48) },
		{ "name": "Whiteboard",     "pos": Vector2(200, 200), "tex": "res://assets/sprites/tiles/wall.png", "size": Vector2(48, 10) },
		{ "name": "Vending",        "pos": Vector2(150, 600), "tex": "res://assets/sprites/tiles/server_rack.png", "size": Vector2(28, 36) },
	]
	for pt in points:
		var container = Node2D.new()
		container.position = pt["pos"]
		container.name = pt["name"]
		_interest_points.add_child(container)

		# Sprite
		var sprite = Sprite2D.new()
		sprite.texture = load(pt["tex"])
		sprite.position = Vector2.ZERO
		sprite.centered = true
		sprite.modulate = Color(1, 1, 1, 0.5)
		sprite.z_index = -1
		container.add_child(sprite)

		# Collision body on layer 1 — player and NPC both detect layer 1
		var body = StaticBody2D.new()
		body.collision_layer = 1
		var col_shape = CollisionShape2D.new()
		var rect = RectangleShape2D.new()
		rect.size = pt["size"]
		col_shape.shape = rect
		body.add_child(col_shape)
		container.add_child(body)

		# Navigation obstacle
		var obs = NavigationObstacle2D.new()
		obs.radius = max(pt["size"].x, pt["size"].y) / 1.5
		container.add_child(obs)

		# Label
		var label = Label.new()
		label.text = pt["name"]
		label.position = Vector2(0, -pt["size"].y / 2 - 16)
		label.add_theme_font_size_override("font_size", 9)
		label.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5, 1))
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		container.add_child(label)

func _spawn_npcs():
	for def in _npc_defs:
		var npc: CyberNPC = _npc_scene.instantiate()
		npc.name = def["id"]
		npc.npc_id = def["id"]
		npc.npc_name = def["name"]
		npc.npc_role = def["role"]
		npc.position = def["pos"]
		npc.move_speed = NPC_SPEED
		npc.get_node("Sprite2D").texture = load(def["tex"])
		_npc_container.add_child(npc)

func _on_npc_list_received(data, error: bool):
	if error:
		print("[Main] Failed to fetch NPC list from backend")
		return
	var npcs = data.get("npcs", [])
	for npc_data in npcs:
		var npc_id = npc_data["npc_id"]
		var node = _npc_container.get_node_or_null(npc_id)
		if node and node is CyberNPC:
			node.npc_id = npc_data["npc_id"]
			node.npc_name = npc_data["name"]
			node.npc_role = npc_data["role"]
