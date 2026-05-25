from fastapi import APIRouter
from pydantic import BaseModel
import random
import logging
import json

router = APIRouter(prefix="/api", tags=["npc_chat"])

_npc_service = None
_action_service = None


def init(npc_service, action_service):
    global _npc_service, _action_service
    _npc_service = npc_service
    _action_service = action_service


class NpcChatRequest(BaseModel):
    npc_id_a: str
    npc_id_b: str


class NpcChatResponse(BaseModel):
    npc_a_line: str
    npc_b_line: str


# All banter in Chinese — 3-5 lines per pair for variety
BANTER: dict[tuple[str, str], list[tuple[str, str]]] = {
    ("npc_zara", "npc_pip"): [
        ("Pip，你又蹲服务器上了。", "Zara！！嘘——我在查 Kron 说的那个内存泄漏。顺便偷点零食，你要吗？"),
        ("Pip，三楼饮水机的事你听说了？", "OMG 你知道什么了？！等等你先别说，让我猜——跟 Nyx 有关对吧？"),
        ("Pip，别以为我不知道你在监控所有人的聊天记录。", "那是诊断需要！！！……好吧，Vex 昨天跟 CEO 说预算的事你感兴趣吗？"),
        ("你怎么又在我的办公室？", "你这里有全楼最好的 wifi！而且我想问你 Kron 最近是不是又没睡觉。"),
    ],
    ("npc_zara", "npc_kron"): [
        ("Kron，Jira 上的 P0 挂了三天了。你看看。", "*猛地惊醒* 啊？！哪个 P0？……哦那个，GC 卡住了我在修。真的在修。"),
        ("你上次说 Q4 搞定，到底哪个 Q4？", "*戳着屏幕* 看见没——协程调度和支付网关之间有个竞态条件。重启能顶一阵子。"),
        ("Kron，你多久没睡了？", "睡？睡眠是给不需要改线上 bug 的人的奢侈品。顺便说，你那个 Slack 加密频道我用了一层额外加密，不客气。"),
    ],
    ("npc_zara", "npc_nyx"): [
        ("Nyx，休息室那个摄像头是你装的？", "*面无表情* 不是。那是咖啡机自带的。我装的那个在三楼天花板。"),
        ("Nyx，最近安保审计查出什么了？", "*递过一份加密文件* 自己看。有人在用打印机传加密数据。不是 Kron。"),
        ("你觉得 Vex 这个人怎么样？", "*沉默三秒* 他的 AR 隐形眼镜每 15 秒截图一次。我已经屏蔽了我的办公室。"),
    ],
    ("npc_zara", "npc_vex"): [
        ("Vex，你的营销预算又超了 200%。", "*灿烂微笑* 那不叫超支，Zara。那叫'前瞻性品牌投资'。措辞很重要，朋友！"),
        ("你的 AR 眼镜在录音。我左眼能检测到。", "*故作惊讶* 这是生产力工具！提升效率的！……行吧，关了关了。"),
        ("Q4 财报你打算怎么跟董事会解释？", "*压低声音* 我们正在'重新定义盈利指标'。搞定了就是创举，搞不定……你想顶 HR 的班吗？"),
    ],
    ("npc_pip", "npc_kron"): [
        ("Kron！！你固件又三个月没更新了！！", "*不抬头* 更新补丁让我偏头痛。而且现在支付系统是稳定的……大概吧。"),
        ("omg Kron 你猜我昨天在服务器日志里发现什么了", "*疯狂敲键盘* Pip 如果又跟 Nyx 的加密流量有关，我不想知道。"),
        ("Kron 我帮你把工资系统的漏洞修了！不用谢！", "*终于抬头了* ……那个后门我留了三年都没人发现，你怎么找到的？"),
        ("你的神经接口是不是又发热了？要我帮你加个散热片吗？", "不是发热的问题……是代码本身在嫌弃我。别碰接口，上次碰完我看到了不该看的。"),
    ],
    ("npc_pip", "npc_nyx"): [
        ("Nyx……那个我看你邮件不是故意的。诊断需要。", "*盯着 Pip 看了五秒* 我知道。我已经把真正的敏感信息放别的地方了。"),
        ("Nyx 你右手那个 EMP 是真的吗？！", "测试我？我可以演示。对准你的零食库存。"),
        ("Nyx，我发现你知道的那个'内鬼'……其实是你自己设计的测试对吧？", "*眯起眼睛* ……聪明。别告诉任何人。特别是 Vex。"),
    ],
    ("npc_pip", "npc_vex"): [
        ("Vex！我上次的'个人品牌'你说能'变现'是什么意思？！", "*调整 AR 眼镜* Pip！一个会修服务器的网红——爆款潜质。咱们合作一波？"),
        ("Vex 你上次让我在别人电脑上装的那个'用户行为分析工具'……", "*立刻打断* 嘘——那叫'客户体验优化套件'。改名之后合规部就通过了。"),
    ],
    ("npc_kron", "npc_nyx"): [
        ("Nyx……我打赌你知道我固件补丁滞后了多少天。", "*面无表情* 三个月零四天。还有你工资系统里那个后门——补上。明天之前。"),
        ("Nyx，上次审计你说'怀疑内部有异常流量'……", "已经定位到你的终端。不是怀疑你——是你被当成跳板了。我已经清理了。下次更新固件。"),
    ],
    ("npc_kron", "npc_vex"): [
        ("Vex，你上次那个'社交媒体增长黑客'……合法吗？", "*眨眼* 合法是一个光谱，Kron。我们坐在光谱的正确那一端。大概。"),
        ("Vex 你让我往 3.2 版本加的那个'用户反馈收集模块'……", "*低声* 那个不叫后门。那个叫'主动用户参与通道'。完全合规。九成合规。"),
    ],
    ("npc_nyx", "npc_vex"): [
        ("Vex，你的 AR 隐形眼镜每一帧都在截图。关掉。", "*投降姿势* 好好好关了——但我得说，你的微表情数据真的很有市场价值。"),
        ("Vex，你再往我的安全报告里塞营销术语我就把你的浏览记录打印出来贴在茶水间。", "*收起笑容* ……你不会。……你会。好吧，成交，别贴。"),
        ("你的办公室有一台我装的音频采集器。把它当成对你的……提醒。", "*脸色变了* ……你到底装了多少个？——算了，我不想知道。"),
    ],
}


@router.post("/npc/npc-chat", response_model=NpcChatResponse)
async def npc_chat(request: NpcChatRequest):
    logger = logging.getLogger("cybertown.npc_chat")
    logger.info(json.dumps({
        "event": "npc_chat_request",
        "npc_id_a": request.npc_id_a,
        "npc_id_b": request.npc_id_b,
    }))

    pair = (request.npc_id_a, request.npc_id_b)
    reverse = (request.npc_id_b, request.npc_id_a)
    lines_list = BANTER.get(pair) or BANTER.get(reverse)

    if lines_list:
        a_line, b_line = random.choice(lines_list)
        if pair not in BANTER:
            a_line, b_line = b_line, a_line
        return NpcChatResponse(npc_a_line=a_line, npc_b_line=b_line)

    return NpcChatResponse(npc_a_line="……", npc_b_line="……")
