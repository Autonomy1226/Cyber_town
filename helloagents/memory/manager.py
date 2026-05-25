from helloagents.memory.short_term import ShortTermMemory
from helloagents.memory.long_term import LongTermMemoryBackend
from helloagents.types import Message, MemoryContext


class MemoryManager:
    """Orchestrates short-term and long-term memory for a single NPC."""

    def __init__(
        self,
        short_term: ShortTermMemory,
        long_term: LongTermMemoryBackend,
        llm_client,
        short_term_window: int = 10,
    ):
        self._short = short_term
        self._long = long_term
        self._llm = llm_client
        self._window = short_term_window

    async def process_turn(self, message: Message) -> MemoryContext:
        embedding = await self._llm.get_embedding(message.content)
        if embedding:
            relevant = await self._long.search(embedding, top_k=5)
            message.embedding = embedding
            await self._long.store(message, embedding)
        else:
            relevant = []
        self._short.add(message)
        recent = self._short.get_last_n(self._window)
        return MemoryContext(
            system_prompt="",
            short_term=recent,
            long_term_relevant=relevant,
            current_message=message.content,
        )

    def store_response(self, response_msg: Message) -> None:
        self._short.add(response_msg)
