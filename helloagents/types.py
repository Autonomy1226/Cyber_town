from dataclasses import dataclass, field
from enum import IntEnum
from datetime import datetime


class FavorabilityLevel(IntEnum):
    HATED = 1       # -100 to -61
    DISLIKED = 2    # -60 to -21
    NEUTRAL = 3     # -20 to 20
    FRIENDLY = 4    # 21 to 60
    TRUSTED = 5     # 61 to 100


@dataclass
class Message:
    role: str                    # "player" | "npc" | "system"
    content: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    embedding: list[float] | None = None


@dataclass
class NPCProfile:
    npc_id: str
    name: str
    role: str
    personality_traits: list[str]
    background: str
    speech_style: str
    private_knowledge: list[str]
    initial_greeting: str
    favorability: int = 0


@dataclass
class MemoryContext:
    system_prompt: str
    short_term: list[Message]
    long_term_relevant: list[Message]
    current_message: str


@dataclass
class AgentResponse:
    npc_id: str
    npc_name: str
    reply: str
    favorability_change: int
    favorability_current: int
    favorability_level: str
