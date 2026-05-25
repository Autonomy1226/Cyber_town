extends CanvasLayer

var _tips = [
	"Zara Chen 在 NexCorp 工作了 12 年，见过三任 CEO 来去。她的左眼是公司强制安装的义体。",
	"Kron-42 已经 72 小时没睡了。他跟代码说话的方式就像在哄一只不听话的宠物。",
	"Nyx Vasquez 的办公室里没有窗户。她说这是'安全需要'。她的盆景叫小安。",
	"Vex Holloway 从初级文案爬到 VP 只用了 18 个月。靠的是才华、勒索和战略性社交。",
	"Pip 的真实姓名没人知道。他们永远蹲在服务器架上，比任何人更早发现 IT 故障。",
	"三楼的饮水机别喝——Pip 说不能告诉你为什么，但听他们的准没错。",
	"休息室那台咖啡机其实是安保部装的监控设备。Nyx 说不是她装的。她装的那个在三楼天花板。",
	"CEO 通过健康项目预算在挪用资金。Zara 有证据，但她在等合适的时机。",
	"这栋楼有一个整层不在地图上。Pip 已经找了三个月还是没找到入口。",
	"Nyx 有所有董事会成员的黑料。她管这叫'保险'。",
	"Kron 在工资系统 3.2 版本里留了一个后门。Pip 找到了，但没说——他们只是在上面多打了一层补丁。",
	"Vex 的 AR 隐形眼镜每 15 秒截图一次。Nyx 已经屏蔽了她的办公室。Vex 还不知道。",
	"打印机旁边那张乱码纸上，有人写了'谁拿了我的订书机？？——Zara'。那是三个月前的。没人还。",
	"Nyx 跟踪一个内鬼已经三个月了。她还没找出是谁——或者说，她已经知道了但还没动手。",
	"Kron 的固件更新滞后了三个月零四天。Nyx 每天数着。",
	"Pip 经营着大楼里的非官方零食走私网络。他们从自动售货机'借用'的。",
	"Vex 曾花钱雇水军搞垮竞争对手的产品发布。这是他们 18 个月内晋升的秘密武器之一。",
	"茶水间 B 区的咖啡机是一台原型监控设备。不是安保部装的。不是 HR 的。那是谁？",
	"每次 NexCorp 有人被裁，Zara 都会在被裁员工的最后一天，假装去茶水间接水。",
	"如果你在 NexCorp 活过了三个月，你就不是新人了——你是幸存者。",
]

var _tip_index: int = 0
var _dot_timer: float = 0.0
var _dots: int = 0
var _tip_timer: float = 0.0
var _progress: float = 0.0

@onready var _spinner: Label = $VBox/Spinner
@onready var _tip_label: Label = $VBox/TipBg/TipLabel
@onready var _progress_bar: ProgressBar = $VBox/ProgressBar

func _ready():
	process_mode = Node.PROCESS_MODE_ALWAYS
	_tips.shuffle()
	_show_tip(0)

	var tip_bg = StyleBoxFlat.new()
	tip_bg.bg_color = Color(0.08, 0.08, 0.12, 0.7)
	tip_bg.set_corner_radius_all(6)
	$VBox/TipBg.add_theme_stylebox_override("panel", tip_bg)

func _process(delta: float):
	_dot_timer += delta
	if _dot_timer > 0.4:
		_dot_timer = 0
		_dots = (_dots + 1) % 4
		var dot_str = ""
		for i in _dots:
			dot_str += "."
		_spinner.text = "正在加载" + dot_str

	_tip_timer += delta
	if _tip_timer > 6.0:
		_tip_timer = 0
		_tip_index = (_tip_index + 1) % _tips.size()
		_show_tip(_tip_index)

	_progress += delta * 0.05
	_progress = min(_progress, 0.9)
	_progress_bar.value = _progress

func _show_tip(idx: int):
	_tip_label.text = _tips[idx]

func finish():
	var bg = $Bg
	var tween = create_tween()
	tween.tween_property(bg, "color:a", 0.0, 0.5)
	tween.tween_property($VBox, "modulate:a", 0.0, 0.5).set_trans(Tween.TRANS_LINEAR)
	tween.tween_callback(queue_free)
