from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    player_id: str = Field(..., min_length=1, max_length=64)
    npc_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=0, max_length=2000)
    context: str | None = None


class ChatResponse(BaseModel):
    npc_id: str
    npc_name: str
    reply: str
    favorability_change: int
    favorability_current: int
    favorability_level: str
    timestamp: float


class NPCInfo(BaseModel):
    npc_id: str
    name: str
    role: str
    position: tuple[float, float]
    current_favorability: int = 0


class NPCListResponse(BaseModel):
    npcs: list[NPCInfo]


class LogEntry(BaseModel):
    timestamp: str
    level: str
    event: str
    npc_id: str | None = None
    player_id: str | None = None
    detail: str | None = None


class LogResponse(BaseModel):
    total: int
    entries: list[LogEntry]
