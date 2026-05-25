# CyberTown / 赛博小镇

一个将 AI 智能体技术与 2D 游戏引擎结合的实验项目——构建一个充满"生命力"的赛博朋克办公室，每个 NPC 都是独立的 AI 智能体。

## 项目概览

```
你（玩家）在 NexCorp 的赛博朋克办公室里自由走动。
按 E 键与任何 NPC 对话，他们会根据自己的性格、记忆和对你的好感度做出回应。
NPC 不是静止的——他们会自主走动、喝咖啡、修服务器、互相闲聊。
```

## 技术架构

```
┌─────────────────┐     HTTP      ┌──────────────┐     Python      ┌──────────────┐
│   Godot 4.6     │ ◄──────────► │   FastAPI     │ ◄────────────► │ HelloAgents  │
│   2D 游戏前端    │   REST API   │   后端服务     │                │  智能体框架   │
├─────────────────┤              ├──────────────┤              ├──────────────┤
│ • 玩家移动控制   │              │ • API 路由     │              │ • SimpleAgent │
│ • NPC 显示&寻路  │              │ • NPC 状态管理 │              │ • 短期记忆     │
│ • 对话 UI       │              │ • 日志系统     │              │ • 长期记忆     │
│ • 场景物件渲染   │              │ • 行为决策     │              │ • 好感度系统   │
└─────────────────┘              └──────────────┘              └──────┬───────┘
                                                                     │
                                                              ┌──────┴───────┐
                                                              │  外部服务     │
                                                              │ • DeepSeek   │
                                                              │ • SQLite     │
                                                              │ • Qdrant(可选)│
                                                              └──────────────┘
```

## 核心功能

### 智能 NPC 对话
与 5 个 NPC 进行自然语言对话。每个 NPC 有独立的角色设定、性格特质和说话风格。对话由 DeepSeek LLM 驱动，NPC 会根据语境和关系做出符合人设的回应。

### 双记忆系统
- **短期记忆**：最近 20 条对话消息（环形缓冲），NPC 记得你刚才说了什么
- **长期记忆**：基于向量相似度检索的历史交互（默认内存模式，可启用 Qdrant 向量数据库）

### 好感度系统
每个 NPC 对玩家有一个 -100 到 +100 的好感度分数，分为 5 个等级：

| 等级 | 分数范围 | NPC 态度 |
|------|----------|----------|
| HATED | -100 ~ -61 | 敌意、轻蔑 |
| DISLIKED | -60 ~ -21 | 冷淡、不耐烦 |
| NEUTRAL | -20 ~ 20 | 职业化、保留 |
| FRIENDLY | 21 ~ 60 | 温暖、合作 |
| TRUSTED | 61 ~ 100 | 开放、分享秘密 |

每次对话后，LLM 会根据玩家态度自动判断好感度变化（-10 ~ +10），NPC 的语气也会随之改变。

### NPC 自主行为
NPC 不只是站着等玩家——他们有自己的"日程"：

- **Kron-42**：大部分时间钉在工位写代码，偶尔去咖啡机
- **Pip**：满办公室跑，最爱服务器房和自动售货机
- **Zara Chen**：工位 ↔ 茶水间 ↔ 办公室巡逻
- **Nyx Vasquez**：办公室周边的"安全巡逻"，很少社交
- **Vex Holloway**：私人办公室 ↔ 会议桌，到处套近乎

两个 NPC 靠近时会显示"正在和 XX 聊天"的气泡。

### 实时日志
所有对话和互动记录到三个地方：控制台（实时）、文件（`backend/data/logs/`）、SQLite 数据库。可通过 API 查询。

## 5 个赛博朋克 NPC

| 名字 | 职位 | 初始好感 | 一句话描述 |
|------|------|----------|-----------|
| **Zara Chen** | HR 主管 | -10 | 厌世老员工，左眼是公司强制装的义眼，抽屉里有清酒 |
| **Kron-42** | 高级软件架构师 | +5 | 72 小时没睡的神经接口开发者，把代码当宠物哄 |
| **Nyx Vasquez** | 首席安全官 | -20 | 前企业反间谍，右手是哑光黑战斗义肢，养了盆盆景 |
| **Vex Holloway** | 市场 VP | +15 | 18 个月从文案爬到 VP，AR 隐形眼镜实时分析你 |
| **Pip** | IT 支持专员 | +25 | 永远蹲在服务器架上吃薯片，知道所有人的秘密 |

## 快速开始

### 1. 环境准备

```bash
# Python 3.10+ (conda)
conda create -n cybertown python=3.10 -y
conda activate cybertown
pip install fastapi uvicorn httpx pydantic pyyaml python-dotenv

# Godot 4.6 — 从 https://godotengine.org 下载
```

### 2. 配置 LLM API Key

```bash
# Windows CMD:
set DEEPSEEK_API_KEY=sk-your-deepseek-key

# 或编辑 config.yaml 直接填入 api_key
```

### 3. 启动后端

```bash
cd D:\Prj\Ai\CyberTown
python run_backend.py
# 服务运行在 http://127.0.0.1:8000
```

### 4. 启动前端

用 Godot 4.6 打开 `godot/` 文件夹，点击运行（F5）。

### 5. 开始游戏

- **WASD** 移动
- **E** 与附近 NPC 对话
- **Esc** 关闭对话框

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 发送对话消息 |
| GET | `/api/npc` | 获取所有 NPC 列表 |
| GET | `/api/npc/{id}` | 获取单个 NPC 信息（含好感度） |
| GET | `/api/npc/actions` | 获取 NPC 当前行为 |
| GET | `/api/logs` | 查询对话日志 |

### 对话请求示例

```json
POST /api/chat
{
    "player_id": "player_001",
    "npc_id": "npc_zara",
    "message": "Zara, 季度考核准备得怎么样了？"
}

// 响应
{
    "npc_id": "npc_zara",
    "npc_name": "Zara Chen",
    "reply": "*叹气，左眼闪过红光* 考核。对。200 份在排队，每次按'解雇原因'排序我的表格就崩。跟管理层说过——人手不够。但至少咖啡机还能用。勉强。",
    "favorability_change": 2,
    "favorability_current": -8,
    "favorability_level": "NEUTRAL",
    "timestamp": 1716500000.123
}
```

## 项目结构

```
CyberTown/
├── helloagents/              # 自研智能体框架
│   ├── agent.py              # SimpleAgent 核心
│   ├── memory/               # 短期 + 长期记忆
│   ├── favorability.py       # 好感度系统
│   ├── llm_client.py         # LLM 客户端 (OpenAI 兼容)
│   └── types.py              # 数据类型定义
├── backend/                  # FastAPI 后端
│   ├── main.py               # 应用入口
│   ├── routes/               # chat / npc / actions / logs
│   ├── services/             # NPC 管理 / 行为决策 / 日志
│   └── npcs/                 # 5 个 NPC 人设定义
├── godot/                    # Godot 4.6 前端
│   ├── scripts/              # GDScript: 玩家/NPC/对话/行为
│   ├── scenes/               # 场景文件
│   └── assets/sprites/       # 32×32 像素占位图
├── config.yaml               # 配置文件
├── run_backend.py            # 后端启动脚本
└── requirements.txt
```

## 配置说明

`config.yaml`:

```yaml
llm:
  base_url: "https://api.deepseek.com/v1"  # LLM API 地址
  model: "deepseek-chat"                   # 模型名
  embedding_model: ""                      # 留空则只使用短期记忆
  temperature: 0.8
  max_tokens: 512

server:
  host: "127.0.0.1"
  port: 8000
```

支持任意 OpenAI 兼容的 API（DeepSeek、OpenAI、Ollama、vLLM 等）。

## 后续方向

- [ ] 启用 Qdrant 向量数据库（长期记忆持久化）
- [ ] NPC 之间 LLM 驱动的真实对话
- [ ] 好感度驱动的任务/剧情系统
- [ ] 玩家状态存档
- [ ] 正经像素美术资源
- [ ] WebSocket 实时推送
- [ ] 多玩家支持
