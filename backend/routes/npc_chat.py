from fastapi import APIRouter
from pydantic import BaseModel
import random
import logging
import json

router = APIRouter(prefix="/api", tags=["npc_chat"])

_npc_service = None
_action_service = None

# Cached banter: {(npc_a, npc_b): [(line_a, line_b), ...]}
_banter_cache: dict[tuple[str, str], list[tuple[str, str]]] = {}
# NPC chat log: list of {timestamp, npc_a, npc_b, line_a, line_b, source}
_chat_log: list[dict] = []
_MAX_LOG = 50

# Fallback Chinese banter — used if LLM generation fails
FALLBACK: dict[tuple[str, str], list[tuple[str, str]]] = {
    ("npc_zara", "npc_kron"): [
        ("Kron，Jira 上的 P0 挂了三天了。", "*惊醒* 啊？哪个 P0？……GC 卡住了我在修。真的。"),
        ("你说 Q4 搞定，哪个 Q4？", "*戳屏幕* 协程和支付网关有个竞态。重启能顶一阵。"),
    ],
    ("npc_zara", "npc_nyx"): [
        ("Nyx，休息室摄像头是你装的？", "*面无波动* 不是。那是咖啡机自带的。我装的在三楼。"),
        ("你觉得 Vex 这人怎么样？", "*沉默三秒* 他的 AR 眼镜每 15 秒截图一次。我屏蔽了我的办公室。"),
    ],
    ("npc_zara", "npc_vex"): [
        ("Vex，营销预算又超了。", "*微笑* 那不叫超支，叫前瞻性品牌投资。措辞很重要。"),
        ("Q4 财报你打算怎么跟董事会说？", "*压低声音* 我们在重新定义盈利指标。搞不定你想顶 HR 的班吗？"),
    ],
    ("npc_zara", "npc_pip"): [
        ("Pip，你又蹲服务器上了。", "Zara！！嘘——我在查 Kron 说的那个内存泄漏。顺便偷点零食，你要吗？"),
        ("Pip，三楼饮水机的事你听说了？", "OMG 你知道什么了？！等等你先别说，让我猜——跟 Nyx 有关对吧？"),
    ],
    ("npc_kron", "npc_nyx"): [
        ("Nyx……你肯定知道我固件滞后了多少天。", "*面无表情* 三个月零四天。工资系统里那个后门——补上。"),
        ("Nyx，你说内部有异常流量……", "已定位到你的终端。不是你——你是跳板。已清理。下次更新固件。"),
    ],
    ("npc_kron", "npc_vex"): [
        ("Vex，你那个'增长黑客'……合法吗？", "*眨眼* 合法是一个光谱。我们在光谱正确那端。大概。"),
        ("Vex，3.2 版加的那个'用户反馈模块'……", "*低声* 那不叫后门，叫主动用户参与通道。九成合规。"),
    ],
    ("npc_kron", "npc_pip"): [
        ("Kron！！你固件又三个月没更新了！！", "*不抬头* 更新让我偏头痛。支付系统是稳定的……大概。"),
        ("omg Kron 你猜我在服务器日志里发现什么了", "*疯狂敲键盘* Pip 如果跟 Nyx 的加密流量有关，我不想知道。"),
        ("Kron 我帮你把工资系统漏洞修了！不用谢！", "*终于抬头* ……那个后门三年没人发现。你怎么找到的？"),
    ],
    ("npc_nyx", "npc_vex"): [
        ("Vex，你的 AR 眼镜在截图。关掉。", "*投降姿势* 好了关了。但你的微表情数据很有市场价值。"),
        ("再往我的安全报告塞营销术语，浏览记录贴茶水间。", "*收起笑容* ……你不会。……你会。好吧成交。"),
        ("你的办公室有我装的一个音频采集器。当提醒。", "*脸色变了* 你到底装了多少？——算了，我不想知道。"),
    ],
    ("npc_nyx", "npc_pip"): [
        ("Nyx……看你邮件不是故意的。诊断需要。", "*盯五秒* 我知道。真正敏感的信息我已经转移了。"),
        ("Nyx 你右手那个 EMP 发射器是真的吗？！", "*冷眼* 测试我？我可以演示。对准你的零食库存。"),
    ],
    ("npc_vex", "npc_pip"): [
        ("Vex！你说我的'个人品牌'能'变现'是什么意思？！", "*调 AR 眼镜* Pip！会修服务器的网红——爆款潜质。合作一波？"),
        ("Vex 你让我在别人电脑装的那个'行为分析工具'……", "*打断* 嘘——那叫客户体验优化套件。改名后合规部通过了。"),
    ],
}

ALL_NPC_IDS = ["npc_zara", "npc_kron", "npc_nyx", "npc_vex", "npc_pip"]

# All 10 unique NPC pairs
NPC_PAIRS = [
    ("npc_zara", "npc_kron"), ("npc_zara", "npc_nyx"), ("npc_zara", "npc_vex"), ("npc_zara", "npc_pip"),
    ("npc_kron", "npc_nyx"), ("npc_kron", "npc_vex"), ("npc_kron", "npc_pip"),
    ("npc_nyx", "npc_vex"), ("npc_nyx", "npc_pip"),
    ("npc_vex", "npc_pip"),
]


def init(npc_service, action_service):
    global _npc_service, _action_service
    _npc_service = npc_service
    _action_service = action_service


async def generate_all_banter():
    """Called once at startup. Generates fresh banter for all NPC pairs via LLM in parallel."""
    global _banter_cache
    logger = logging.getLogger("cybertown.npc_chat")

    # Immediately use fallback so server is ready instantly
    _banter_cache = dict(FALLBACK)

    llm = _npc_service._llm_client if _npc_service else None
    if not llm or not llm._config.api_key:
        logger.info("No LLM configured, using fallback banter (%d pairs)", len(_banter_cache))
        return

    logger.info("Starting parallel banter generation for %d NPC pairs...", len(NPC_PAIRS))

    async def generate_pair(a_id, b_id):
        try:
            agent_a = _npc_service.get_agent(a_id)
            agent_b = _npc_service.get_agent(b_id)
        except KeyError:
            return

        prompt = f"""你是赛博朋克办公室的叙事生成器。为下面两个角色写 5 组简短的碰面对话（每人一句）。所有对话必须用中文。每句话 5-20 个字。

角色A: {agent_a.profile.name} ({agent_a.profile.role})
性格: {', '.join(agent_a.profile.personality_traits)}
说话: {agent_a.profile.speech_style}

角色B: {agent_b.profile.name} ({agent_b.profile.role})
性格: {', '.join(agent_b.profile.personality_traits)}
说话: {agent_b.profile.speech_style}

输出纯JSON数组（不要markdown，不要说别的）：
[
  ["A说的话（中文）", "B说的话（中文）"],
  ...
]"""

        try:
            raw = await llm.chat([
                {"role": "system", "content": "Output ONLY valid JSON array of Chinese dialogue. No markdown. No explanation."},
                {"role": "user", "content": prompt},
            ])
            raw = raw.strip()
            if raw.startswith("```"):
                import re
                raw = re.sub(r'^```\w*\n?', '', raw)
                raw = re.sub(r'\n?```$', '', raw)
            lines = json.loads(raw)
            pairs = [(str(p[0]), str(p[1])) for p in lines if len(p) == 2]
            if pairs:
                _banter_cache[(a_id, b_id)] = pairs
                logger.info("Generated %d lines for %s <-> %s", len(pairs), a_id, b_id)
        except Exception as e:
            logger.warning("Banter failed for %s<->%s: %s", a_id, b_id, e)

    # Run all pairs in parallel
    import asyncio
    tasks = [generate_pair(a, b) for a, b in NPC_PAIRS]
    await asyncio.gather(*tasks)

    total = sum(len(v) for v in _banter_cache.values())
    logger.info("Banter generation done: %d lines across %d pairs", total, len(_banter_cache))


class NpcChatRequest(BaseModel):
    npc_id_a: str
    npc_id_b: str


class NpcChatResponse(BaseModel):
    npc_a_line: str
    npc_b_line: str


@router.post("/npc/npc-chat", response_model=NpcChatResponse)
async def npc_chat(request: NpcChatRequest):
    import time
    pair = (request.npc_id_a, request.npc_id_b)
    reverse = (request.npc_id_b, request.npc_id_a)
    a_line = b_line = ""
    source = "cache"

    # --- 15% chance: use LLM for fresh dialogue ---
    if random.random() < 0.15 and _npc_service and _npc_service._llm_client:
        llm = _npc_service._llm_client
        if llm._config.api_key:
            try:
                agent_a = _npc_service.get_agent(request.npc_id_a)
                agent_b = _npc_service.get_agent(request.npc_id_b)
                prompt = f"""{agent_a.profile.name}和{agent_b.profile.name}在办公室碰面了。给他们写一句简短的对话（各一句，中文）。
{agent_a.profile.name}性格: {', '.join(agent_a.profile.personality_traits)}
{agent_b.profile.name}性格: {', '.join(agent_b.profile.personality_traits)}
输出纯JSON: ["A的话", "B的话"]"""
                raw = await llm.chat([
                    {"role": "system", "content": "Output ONLY a JSON array of 2 strings. No markdown."},
                    {"role": "user", "content": prompt},
                ])
                raw = raw.strip().strip("```").strip()
                lines = json.loads(raw)
                if len(lines) == 2:
                    a_line, b_line = str(lines[0]), str(lines[1])
                    source = "llm"
            except Exception:
                pass  # fall through to cache

    # --- Cache / Fallback ---
    if not a_line:
        lines = _banter_cache.get(pair) or _banter_cache.get(reverse)
        if lines:
            a_line, b_line = random.choice(lines)
            if pair not in _banter_cache:
                a_line, b_line = b_line, a_line
        else:
            fb = FALLBACK.get(pair) or FALLBACK.get(reverse)
            if fb:
                a_line, b_line = random.choice(fb)
                if pair not in FALLBACK:
                    a_line, b_line = b_line, a_line
            else:
                a_line, b_line = "……", "……"

    # Log it
    _chat_log.append({
        "timestamp": time.time(),
        "npc_a": request.npc_id_a,
        "npc_b": request.npc_id_b,
        "line_a": a_line,
        "line_b": b_line,
        "source": source,
    })
    if len(_chat_log) > _MAX_LOG:
        _chat_log.pop(0)

    return NpcChatResponse(npc_a_line=a_line, npc_b_line=b_line)


@router.get("/npc/chat-log")
async def get_chat_log():
    return {"entries": list(reversed(_chat_log))}
