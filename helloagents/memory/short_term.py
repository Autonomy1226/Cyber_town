from collections import deque
from helloagents.types import Message


class ShortTermMemory:
    """Fixed-size circular buffer of recent conversation messages."""

    def __init__(self, max_size: int = 20):
        self._buffer: deque[Message] = deque(maxlen=max_size)

    def add(self, message: Message) -> None:
        self._buffer.append(message)

    def get_all(self) -> list[Message]:
        return list(self._buffer)

    def get_last_n(self, n: int) -> list[Message]:
        buffer_list = list(self._buffer)
        return buffer_list[-n:]

    def clear(self) -> None:
        self._buffer.clear()

    def to_context_string(self) -> str:
        lines = []
        for msg in self._buffer:
            lines.append(f"[{msg.role.upper()}]: {msg.content}")
        return "\n".join(lines)
