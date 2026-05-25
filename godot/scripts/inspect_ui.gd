extends CanvasLayer

@onready var _name_label: Label = $Panel/VBox/NameLabel
@onready var _role_label: Label = $Panel/VBox/RoleLabel
@onready var _fav_label: Label = $Panel/VBox/FavLabel
@onready var _traits_label: Label = $Panel/VBox/TraitsLabel
@onready var _activity_label: Label = $Panel/VBox/ActivityLabel
@onready var _backstory_label: Label = $Panel/VBox/BackstoryLabel

var _npc_colors = {
	"npc_zara": Color(0.78, 0.24, 0.24, 1),
	"npc_kron": Color(0.24, 0.71, 0.24, 1),
	"npc_nyx":  Color(0.5, 0.5, 0.5, 1),
	"npc_vex":  Color(0.78, 0.63, 0.16, 1),
	"npc_pip":  Color(0.86, 0.47, 0.86, 1),
}

func _ready():
	var bg = StyleBoxFlat.new()
	bg.bg_color = Color(0.06, 0.06, 0.1, 0.93)
	bg.set_corner_radius_all(10)
	$Panel.add_theme_stylebox_override("panel", bg)

func show_npc(npc_id: String):
	ApiClient.fetch_npc_info(npc_id, func(data, err):
		if err:
			return
		var name = data.get("name", "???")
		var role = data.get("role", "")
		var fav = data.get("current_favorability", 0)
		var color = _npc_colors.get(npc_id, Color.WHITE)
		var level = _fav_level(fav)

		_name_label.text = name
		_name_label.add_theme_color_override("font_color", color)
		_role_label.text = role
		_fav_label.text = "好感度: " + level + " (" + str(fav) + ")"
		_traits_label.text = ""

		# Find NPC node for current activity
		var npcs = get_tree().get_nodes_in_group("npc")
		for n in npcs:
			if n is CyberNPC and n.npc_id == npc_id:
				_activity_label.text = "正在: " + n.current_action.get("dialogue_line", "发呆...")
				break

		visible = true
	)

func _fav_level(score: int) -> String:
	if score <= -61: return "HATED"
	if score <= -21: return "DISLIKED"
	if score <= 20: return "NEUTRAL"
	if score <= 60: return "FRIENDLY"
	return "TRUSTED"

func _input(event: InputEvent):
	if visible and (event.is_action_pressed("inspect") or event.is_action_pressed("ui_cancel")):
		hide()
