# CyberTown / 赛博小镇

将 AI 智能体技术与 2D 游戏引擎结合——在赛博朋克办公室里，每个 NPC 都是一个拥有记忆、性格和情感的独立 AI 智能体。他们会自主走动、互相闲聊、被上司训话、摸鱼划水。你（玩家）可以和任何人自由对话，你的每一句话都会影响他们对你的态度。

## 项目概览

你走进 NexCorp 的办公室。HR 主管 Zara 在批离职文件，程序员 Kron 已经 72 小时没睡了，安全官 Nyx 在巡逻，市场 VP Vex 在白板前画永远右上角的增长曲线，IT 专员 Pip 蹲在服务器架上修东西。你可以走过去跟任何人聊天，也可以翻翻打印机、在售货机买零食、去白板画个笑脸。Zara 偶尔会喊下属去办公室训话。你走到办公室底部门口可以去大厅。

## 技术架构

```
┌──────────────────┐     HTTP       ┌───────────────┐     Python      ┌─────────────────┐
│   Godot 4.6      │ ◄───────────► │    FastAPI     │ ◄────────────► │  HelloAgents    │
│   2D 游戏前端     │   REST API    │   后端服务      │                │  智能体框架      │
├──────────────────┤               ├───────────────┤               ├─────────────────┤
│ • WASD 玩家移动   │               │ • /api/chat    │               │ • SimpleAgent   │
│ • NPC 自主寻路    │               │ • /api/npc/*   │               │ • 短期记忆(Deque)│
│ • 对话 UI + 背包  │               │ • /api/player  │               │ • 长期记忆(向量) │
│ • 场景物件交互     │               │ • /api/object  │               │ • 好感度(-100~100)│
│ • 多场景切换      │               │ • /api/history │               │ • LLM SystemPrompt│
└──────────────────┘               └──────┬────────┘               └────────┬────────┘
                                          │                                 │
                                   ┌──────┴────────┐               ┌───────┴────────┐
                                   │   SQLite       │               │   DeepSeek V4  │
                                   │ • 对话历史      │               │ • Chat API     │
                                   │ • 好感度持久化   │               │ • 兼容 OpenAI   │
                                   │ • 操作日志      │               └────────────────┘
                                   └───────────────┘
```

---

# HelloAgents 智能体框架详解

HelloAgents 是本项目的核心——一个轻量级的 AI 智能体框架，每个 NPC 都是一个 `SimpleAgent` 实例。

## 架构概览

```
                    ┌──────────────────────────────────┐
                    │          SimpleAgent              │
                    │  ┌──────────────────────────────┐ │
玩家消息 ──────────► │  │         respond()            │ │ ──► AgentResponse
                    │  │  1. 创建 Message              │ │     • npc_name
                    │  │  2. MemoryManager.process()   │ │     • reply
                    │  │  3. 构建 SystemPrompt         │ │     • favorability_change
                    │  │  4. 组装 LLM Messages         │ │     • favorability_current
                    │  │  5. LLM.chat()               │ │     • favorability_level
                    │  │  6. 解析 [FAV:±N] 标签        │ │
                    │  │  7. 更新好感度                 │ │
                    │  │  8. 存储回复到短期记忆          │ │
                    │  └──────────────────────────────┘ │
                    │                                    │
                    │  依赖：                             │
                    │  • NPCProfile (人设)               │
                    │  • MemoryManager (记忆)            │
                    │  • FavorabilitySystem (好感度)     │
                    │  • LLMClient (大模型调用)          │
                    └──────────────────────────────────┘
```

## 1. SimpleAgent — 智能体核心

文件：`helloagents/agent.py`

```python
class SimpleAgent:
    profile: NPCProfile          # 角色人设
    memory: MemoryManager        # 记忆管理器
    favorability: FavorabilitySystem  # 好感度系统
    _llm: LLMClient              # LLM 客户端
```

**核心方法 `respond(player_message) -> AgentResponse`：**

1. 将玩家消息包装为 `Message(role="player", content=...)` 
2. 调用 `MemoryManager.process_turn()`：嵌入消息 → 检索长期记忆 → 存入短期记忆 → 返回上下文
3. 调用 `_build_system_prompt()`：用 NPC 人设 + 好感度等级 + 对话规则拼装 System Prompt
4. 调用 `_assemble_llm_messages()`：组装完整的 LLM 请求消息列表（System + 历史记忆 + 当前对话）
5. 调用 `LLMClient.chat()` 请求大模型生成回复
6. 解析回复中的 `[FAV:±N]` 标签，提取好感度变化量
7. 更新好感度分数
8. 将 NPC 回复存入短期记忆
9. 返回 `AgentResponse(回复文本, 好感度变化, 当前好感度, 等级)`

**System Prompt 构建**：

每个 NPC 的 System Prompt 由以下部分组成：
- 基础身份：`"You are {name}, a {role} in a cyberpunk office."`
- 背景故事：NPC 的前世今生（12 年 HR 经历、72 小时没睡...）
- 性格特质：逗号分隔的性格标签（jaded, sarcastic, paranoid...）
- 说话风格：具体的语言特征描述（"Dry corporate deadpan with dark humor"）
- 私密知识：NPC 的独家秘密（CEO 挪用资金、工资系统有后门...）
- **当前好感度等级**：动态注入，决定 NPC 当前的态度基调
- **6 条对话规则**：
  1. 永远不打破角色
  2. 回复简洁（1-3 句）
  3. 根据好感度调整语气（HATED=敌意 → TRUSTED=开放）
  4. 回复开头加 `[FAV:N]` 标签（LLM 自评好感度影响）
  5. 不提及好感度标签
  6. 用中文回复

**好感度标签机制**：

这是框架中最精巧的设计之一。LLM 在生成回复时，需要在开头加上 `[FAV:+3]` 或 `[FAV:-5]` 这样的标签，表示玩家这句话对 NPC 态度的影响。好处是：
- 不需要额外的情感分析 API 调用
- LLM 天然理解语义，能准确判断态度变化
- 标签在显示给玩家前被正则移除，玩家看不到

## 2. MemoryManager — 双记忆系统

文件：`helloagents/memory/manager.py`

```
MemoryManager
├── ShortTermMemory   (短期记忆)
│   └── collections.deque, maxlen=20
│   └── 存储最近 20 条 Message
│   └── 随会话结束而清空（重启后可预加载）
└── LongTermMemoryBackend (长期记忆，抽象接口)
    ├── InMemoryLongTermMemory (默认)
    │   └── 暴力余弦相似度搜索
    │   └── 适合单次游戏会话
    └── QdrantLongTermMemory (可选)
        └── Qdrant 向量数据库
        └── 支持海量历史消息的语义检索
```

**处理流程 `process_turn(message) -> MemoryContext`：**

1. 调用 `LLMClient.get_embedding(text)` 获取消息的向量嵌入
2. 用嵌入向量在长期记忆中搜索 top-5 最相似的历史消息
3. 将当前消息存入短期记忆
4. 异步存入长期记忆
5. 返回 `MemoryContext(system_prompt, short_term[], long_term_relevant[], current_message)`

**持久化恢复**：

后端重启后，NPC 的短期记忆为空。系统会自动从 SQLite `chat_history` 表加载该玩家与此 NPC 的最近 10 条对话，注入短期记忆。这样 NPC 不会"失忆"。

## 3. FavorabilitySystem — 好感度系统

文件：`helloagents/favorability.py`

| 等级 | ENUM | 分数范围 | NPC 语气 |
|------|------|----------|----------|
| HATED | 1 | -100 ~ -61 | 敌意、轻蔑、攻击性 |
| DISLIKED | 2 | -60 ~ -21 | 冷淡、讽刺、不耐烦 |
| NEUTRAL | 3 | -20 ~ 20 | 职业化、保留、公事公办 |
| FRIENDLY | 4 | 21 ~ 60 | 温暖、合作、愿意帮忙 |
| TRUSTED | 5 | 61 ~ 100 | 开放友好、可能分享秘密 |

- 分数变化 △ ∈ [-10, +10]，由 LLM 根据玩家话语判断
- 分数变化被 clamp 在范围内
- 等级直接影响 System Prompt 中的语气指令
- 好感度持久化到 SQLite `favorability` 表，重启不丢失

## 4. LLMClient — 大模型客户端

文件：`helloagents/llm_client.py`

- **chat(messages)**：发送 Chat Completion 请求，返回文本。兼容 OpenAI API 格式（DeepSeek、OpenAI、Ollama、vLLM 等）
- **get_embedding(text)**：获取文本的向量嵌入。如果未配置 embedding model（如 DeepSeek），返回空列表，跳过长期记忆检索
- 异步 HTTP（httpx），支持超时和 API Key 配置

## 5. 数据类型

文件：`helloagents/types.py`

```python
Message       # role, content, timestamp, embedding
NPCProfile    # npc_id, name, role, personality_traits[], background, speech_style, private_knowledge[], initial_greeting, favorability
MemoryContext # system_prompt, short_term[], long_term_relevant[], current_message
AgentResponse # npc_id, npc_name, reply, favorability_change, favorability_current, favorability_level
```

## 数据流全景

```
玩家在 Godot 输入 "Zara，季度报告怎么样了？"
    │
    ▼
Godot 发送 POST /api/chat { player_id, npc_id, message }
    │
    ▼
FastAPI chat.py 路由接收请求
    │
    ├─► NPCService.preload_memory()     # 首次对话：从 SQLite 预加载历史
    ├─► NPCService.get_favorability()    # 获取该玩家对此 NPC 的好感度
    │
    ▼
SimpleAgent.respond("Zara，季度报告怎么样了？")
    │
    ├─► MemoryManager.process_turn()
    │   ├─► LLMClient.get_embedding()    → embedding (DeepSeek 跳过)
    │   ├─► LongTermMemory.search()      → 5 条相关历史
    │   └─► ShortTermMemory.add()        → 存入短期缓冲
    │
    ├─► _build_system_prompt()
    │   → "You are Zara Chen, Head of HR... RELATIONSHIP: NEUTRAL (-8)..."
    │
    ├─► _assemble_llm_messages()
    │   → [system, "CONVERSATION HISTORY:...", user:"你刚才说...", assistant:"..."]
    │
    ├─► LLMClient.chat(messages)
    │   → "[FAV:+2] *叹气，左眼红光一闪* 季度报告？200 份文件在等我..."
    │
    ├─► _parse_favorability_tag()
    │   → delta=+2, clean="*叹气，左眼红光一闪* 季度报告？..."
    │
    ├─► FavorabilitySystem.apply_delta(+2)
    │   → score: -10 → -8
    │
    └─► MemoryManager.store_response()
    │
    ▼
FastAPI 返回 ChatResponse { reply, favorability_change: +2, favorability_current: -8, ... }
    │
    ▼
Godot 显示 NPC 回复，好感度条更新
```

---

## 游戏系统

### NPC 自主行为

每个 NPC 有独立的**加权随机行程表**。`/api/npc/actions` 每 10 秒轮询一次：

| NPC | 工位 | 巡逻 | 咖啡 | 社交 | 特殊行为 |
|-----|------|------|------|------|----------|
| **Zara** | 35% | 3% | 12% | 5% | **命令下属 26%** |
| **Kron** | 65% | 4% | 13% | 0% | 查服务器 12% |
| **Nyx** | 20% | 45% | 5% | 0% | 查服务器 20% |
| **Vex** | 15% | 5% | 12% | 22% | 白板战略 16% |
| **Pip** | 15% | 8% | 12% | 21% | 修服务器 22% |

每个 NPC 有**专属活动标签**（在头上显示）：
- Zara：`"处理离职文件..."`、`"续命咖啡...第四杯了"`
- Kron：`"修 Bug...72小时没睡了"`、`"紧急补充咖啡因..."`
- Nyx：`"安全巡逻..."`、`"检查入侵痕迹..."`
- Vex：`"画增长曲线...全是右上"`、`"在咖啡机旁'偶遇'同事..."`
- Pip：`"偷偷加补丁...Kron还没发现"`、`"拆装无人机零件..."`

### 主管指挥系统

Zara（HR 主管）可以命令其他 NPC：
- Zara 头顶冒泡 `"去把报告给我整理好，现在。"`
- 下属回应 `"……知道了。马上。"` 并走向 Zara 工位
- 5 种命令 × 5 种回应，随机组合

### NPC 间对话

两个 NPC 靠近到 75px 内时自动触发对话。后端启动时通过 LLM 批量生成 10 组 NPC 对的台词并缓存（或用预写中文台词），全程不消耗额外 token。

### 经济 & 物品系统

- **初始资金**：$50
- **10 种物品**：能量饮料、咖啡券、加密U盘、旧电路板、数据碎片、员工ID卡、黑客工具、清酒壶、神经补丁、营销报告
- **6 个可互动物品**：咖啡机、自动售货机、打印机、服务器机柜、白板、饮水机
- 按 `F` 互动物品，按 `I` 打开背包

### 场景切换

- **办公室**（主场景）：NexCorp 办公区，5 个 NPC + 所有设施
- **大厅**（第二场景）：过渡区域，30×20 格
- 走到场景边缘的门触发切换，带加载界面和小提示

### 数据持久化

| 数据类型 | 存储位置 | 重启保留 |
|----------|----------|----------|
| 对话历史 | SQLite `chat_history` | ✓ |
| 好感度 | SQLite `favorability` | ✓ |
| 短期记忆 | 服务器内存 | ✗ (但从 SQLite 预加载 10 条) |
| NPC 对话缓存 | 服务器内存 | ✗ |
| 玩家背包/金钱 | 服务器内存 | ✗ |

---

## 5 个赛博朋克 NPC

| 名字 | 职位 | 初始好感 | 背景故事 |
|------|------|----------|----------|
| **Zara Chen** | HR 主管 | -10 | 在 NexCorp 12 年，见过三任 CEO。左眼是公司强装的义体。抽屉里有清酒。秘密运营工会 Slack。 |
| **Kron-42** | 高级软件架构师 | +5 | 72 小时没睡的神经接口开发者。跟代码说话像哄宠物。工资系统 3.2 版留了后门。 |
| **Nyx Vasquez** | 首席安全官 | -20 | 前企业反间谍。右手是哑光黑战斗义肢（内置 EMP）。办公室没窗户。盆景叫"小安"。 |
| **Vex Holloway** | 市场 VP | +15 | 18 个月从文案爬到 VP。AR 隐形眼镜实时分析对话对象。雇水军搞垮过竞品。 |
| **Pip** | IT 支持专员 | +25 | 真名不详。永远蹲在服务器架上。经营大楼非官方零食走私网。偷偷修 Nyx 团队的安全漏洞。 |

---

## 快速开始

```bash
# 环境
conda create -n cybertown python=3.10 -y && conda activate cybertown
pip install fastapi uvicorn httpx pydantic pyyaml

# 配置 API Key (Windows CMD)
set DEEPSEEK_API_KEY=sk-your-key

# 启动后端
cd D:\Prj\Ai\CyberTown && python run_backend.py
# → http://127.0.0.1:8000

# 前端：Godot 4.6 打开 godot/ 文件夹，F5 运行
```

**操作**：WASD 移动 | E 对话 NPC | F 互动物品 | I 背包 | Esc 关闭面板

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | NPC 对话（含上下文） |
| GET | `/api/npc` | NPC 列表 |
| GET | `/api/npc/{id}` | 单个 NPC 信息 + 好感度 |
| GET | `/api/npc/actions` | NPC 当前行为（寻路目标） |
| POST | `/api/npc/npc-chat` | NPC 间对话 |
| GET/POST | `/api/history/*` | 对话历史存取 |
| GET | `/api/player/{id}` | 玩家背包 + 金钱 |
| GET | `/api/object/list` | 可互动物品列表 |
| POST | `/api/object/interact` | 物品互动 |
| GET | `/api/logs` | 操作日志查询 |

## 项目结构

```
CyberTown/
├── helloagents/                 # 自研 AI 智能体框架
│   ├── agent.py                 # SimpleAgent — 核心智能体
│   ├── memory/                  # 双记忆系统
│   │   ├── short_term.py        #   短期：Deque 环形缓冲 (max 20)
│   │   ├── long_term.py         #   长期：InMemory/Qdrant 向量搜索
│   │   └── manager.py           #   管理器：嵌入→检索→存储→组装
│   ├── favorability.py          # 好感度系统 (-100~100, 5 级)
│   ├── llm_client.py            # LLM 客户端 (OpenAI 兼容)
│   └── types.py                 # Message/NPCProfile/AgentResponse
├── backend/                     # FastAPI 后端
│   ├── main.py                  # 应用入口 + lifespan
│   ├── routes/                  # chat / npc / actions / npc_chat / history / player / objects
│   ├── services/                # npc_service / action_service / log_service / economy_service
│   └── npcs/personalities.py    # 5 个 NPC 完整人设
├── godot/                       # Godot 4.6 前端
│   ├── scripts/                 # 12 个 GDScript
│   ├── scenes/                  # 8 个场景文件
│   └── assets/sprites/          # 32×32 像素占位图
├── config.yaml                  # LLM 配置
├── run_backend.py
└── requirements.txt
```
