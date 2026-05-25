extends Node2D

const TILE_SIZE: int = 32
const WORLD_W: int = 40
const WORLD_H: int = 23
const NPC_SPEED: float = 80.0

var _npc_scene: PackedScene = preload("res://scenes/npc.tscn")
var _inv_ui_scene: PackedScene = preload("res://scenes/inventory_ui.tscn")
var _obj_ui_scene: PackedScene = preload("res://scenes/object_ui.tscn")
var _loading_scene: PackedScene = preload("res://scenes/loading_screen.tscn")
var _loading_screen = null

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
@onready var _nav_region: NavigationRegion2D = $NavigationRegion2D
@onready var _interest_points: Node2D = $InterestPoints
@onready var _npc_container: Node2D = $NPCs

func _ready():
	# Show loading screen immediately
	_loading_screen = _loading_scene.instantiate()
	add_child(_loading_screen)

	_generate_floor()
	_setup_navigation()
	_build_boundaries()
	_build_doors()
	_spawn_interest_points()
	_spawn_npcs()
	_spawn_ui()

	# Position player at spawn point or default
	var player = $Player
	if player and Globals.spawn_marker:
		var sp = $SpawnPoints.get_node_or_null(Globals.spawn_marker)
		if sp:
			player.position = sp.position
	Globals.spawn_marker = ""

	ApiClient.fetch_npcs(_on_npc_list_received)

func _generate_floor():
	for x in range(WORLD_W):
		for y in range(WORLD_H):
			_ground_layer.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))

func _build_boundaries():
	# Invisible walls around the map edges
	var world_w = WORLD_W * TILE_SIZE
	var world_h = WORLD_H * TILE_SIZE
	var wall_thickness = 16.0

	var edges = [
		{ "pos": Vector2(world_w / 2, -wall_thickness / 2), "size": Vector2(world_w, wall_thickness) },      # top
		{ "pos": Vector2(world_w / 2, world_h + wall_thickness / 2), "size": Vector2(world_w, wall_thickness) }, # bottom
		{ "pos": Vector2(-wall_thickness / 2, world_h / 2), "size": Vector2(wall_thickness, world_h) },          # left
		{ "pos": Vector2(world_w + wall_thickness / 2, world_h / 2), "size": Vector2(wall_thickness, world_h) }, # right
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

func _build_doors():
	var doors = [
		{ "pos": Vector2(640, 710), "size": Vector2(80, 14), "target": "res://scenes/lobby.tscn", "label": "» 大厅", "spawn": "from_office" },
	]
	for d in doors:
		var container = Node2D.new()
		container.position = d["pos"]
		container.name = "Door"
		add_child(container)

		var zone = Area2D.new()
		zone.name = "Trigger"
		zone.add_to_group("doors")
		zone.set_meta("target_scene", d["target"])
		zone.set_meta("spawn_marker", d["spawn"])
		var shape = CollisionShape2D.new()
		var rect = RectangleShape2D.new()
		rect.size = d["size"]
		shape.shape = rect
		zone.add_child(shape)
		container.add_child(zone)

		var label = Label.new()
		label.text = d["label"]
		label.position = Vector2(0, -16)
		label.add_theme_font_size_override("font_size", 11)
		label.add_theme_color_override("font_color", Color(0.3, 0.9, 1, 0.8))
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		container.add_child(label)

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
	# NPC desks
		{ "id": "desk_zara", "name": "Zara 的工位", "pos": Vector2(320, 600), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(56, 32) },
		{ "id": "desk_kron", "name": "Kron 的工位", "pos": Vector2(640, 400), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(64, 36) },
		{ "id": "desk_nyx",  "name": "Nyx 的办公室", "pos": Vector2(960, 250), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(56, 32) },
		{ "id": "desk_vex",  "name": "Vex 的办公室", "pos": Vector2(160, 350), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(60, 34) },
		{ "id": "desk_pip",  "name": "Pip 的工位", "pos": Vector2(800, 650), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(52, 30) },
		# Shared objects
		{ "id": "coffee_machine", "name": "咖啡机", "pos": Vector2(500, 200), "tex": "res://assets/sprites/tiles/plant.png", "size": Vector2(24, 24) },
		{ "id": "water_cooler", "name": "饮水机", "pos": Vector2(500, 550), "tex": "res://assets/sprites/tiles/plant.png", "size": Vector2(24, 24) },
		{ "id": "printer", "name": "打印机", "pos": Vector2(700, 200), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(48, 24) },
		{ "id": "meeting_table", "name": "会议桌", "pos": Vector2(500, 300), "tex": "res://assets/sprites/tiles/desk.png", "size": Vector2(80, 40) },
		{ "id": "server_rack", "name": "服务器机柜", "pos": Vector2(1050, 600), "tex": "res://assets/sprites/tiles/server_rack.png", "size": Vector2(28, 48) },
		{ "id": "whiteboard", "name": "白板", "pos": Vector2(200, 200), "tex": "res://assets/sprites/tiles/wall.png", "size": Vector2(48, 10) },
		{ "id": "vending", "name": "自动售货机", "pos": Vector2(150, 600), "tex": "res://assets/sprites/tiles/server_rack.png", "size": Vector2(28, 36) },
	]
	for pt in points:
		var container = Node2D.new()
		container.position = pt["pos"]
		container.name = pt["name"]
		_interest_points.add_child(container)

		var sprite = Sprite2D.new()
		sprite.texture = load(pt["tex"])
		sprite.position = Vector2.ZERO
		sprite.centered = true
		sprite.modulate = Color(1, 1, 1, 0.5)
		sprite.z_index = -1
		container.add_child(sprite)

		var body = StaticBody2D.new()
		body.collision_layer = 1
		var col_shape = CollisionShape2D.new()
		var rect = RectangleShape2D.new()
		rect.size = pt["size"]
		col_shape.shape = rect
		body.add_child(col_shape)
		container.add_child(body)

		var obs = NavigationObstacle2D.new()
		obs.radius = max(pt["size"].x, pt["size"].y) / 1.5
		container.add_child(obs)

		var zone = Area2D.new()
		zone.name = "InteractZone"
		zone.add_to_group("interactable")
		zone.set_meta("object_id", pt["id"])
		zone.set_meta("label", pt["name"])
		var zone_shape = CollisionShape2D.new()
		var circle = CircleShape2D.new()
		circle.radius = 60.0
		zone_shape.shape = circle
		zone.add_child(zone_shape)
		container.add_child(zone)

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

func _spawn_ui():
	var inv = _inv_ui_scene.instantiate()
	inv.name = "InventoryUI"
	add_child(inv)

	var obj = _obj_ui_scene.instantiate()
	obj.name = "ObjectUI"
	add_child(obj)

	var iu = load("res://scenes/inspect_ui.tscn").instantiate()
	iu.name = "InspectUI"
	add_child(iu)

	var cl = load("res://scenes/chatlog_ui.tscn").instantiate()
	cl.name = "ChatLogUI"
	add_child(cl)

func _on_npc_list_received(data, error: bool):
	if error:
		return
	var npcs = data.get("npcs", [])
	for npc_data in npcs:
		var npc_id = npc_data["npc_id"]
		var node = _npc_container.get_node_or_null(npc_id)
		if node and node is CyberNPC:
			node.npc_id = npc_data["npc_id"]
			node.npc_name = npc_data["name"]
			node.npc_role = npc_data["role"]

	# Hide loading screen
	if _loading_screen:
		_loading_screen.finish()
		_loading_screen = null
