from abc import ABC, abstractmethod
from helloagents.types import Message


class LongTermMemoryBackend(ABC):
    @abstractmethod
    async def store(self, message: Message, embedding: list[float]) -> None:
        ...

    @abstractmethod
    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[Message]:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...


class InMemoryLongTermMemory(LongTermMemoryBackend):
    """Fallback: stores embeddings in a plain list with brute-force cosine search."""

    def __init__(self, embedding_dim: int = 1536):
        self._dim = embedding_dim
        self._messages: list[Message] = []
        self._embeddings: list[list[float]] = []

    async def store(self, message: Message, embedding: list[float]) -> None:
        self._messages.append(message)
        self._embeddings.append(embedding)

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[Message]:
        if not self._messages:
            return []
        scores = [self._cosine_sim(query_embedding, emb) for emb in self._embeddings]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [self._messages[i] for i, _ in ranked[:top_k]]

    async def clear(self) -> None:
        self._messages.clear()
        self._embeddings.clear()

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = (sum(x * x for x in a)) ** 0.5
        norm_b = (sum(x * x for x in b)) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


class QdrantLongTermMemory(LongTermMemoryBackend):
    """Production backend using Qdrant vector DB."""

    def __init__(self, url: str, collection_name: str, embedding_dim: int = 1536):
        self._url = url
        self._collection = collection_name
        self._dim = embedding_dim
        self._client = None
        self._initialized = False

    async def _ensure_collection(self):
        if self._initialized:
            return
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        self._client = QdrantClient(url=self._url)
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._dim, distance=Distance.COSINE),
            )
        self._initialized = True

    async def store(self, message: Message, embedding: list[float]) -> None:
        await self._ensure_collection()
        from qdrant_client.models import PointStruct
        import uuid
        point_id = str(uuid.uuid4())
        self._client.upsert(
            collection_name=self._collection,
            points=[PointStruct(
                id=point_id,
                vector=embedding,
                payload={"role": message.role, "content": message.content, "timestamp": message.timestamp},
            )],
        )

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[Message]:
        await self._ensure_collection()
        results = self._client.search(
            collection_name=self._collection,
            query_vector=query_embedding,
            limit=top_k,
        )
        messages = []
        for r in results:
            payload = r.payload
            messages.append(Message(
                role=payload.get("role", "unknown"),
                content=payload.get("content", ""),
                timestamp=payload.get("timestamp", 0),
            ))
        return messages

    async def clear(self) -> None:
        await self._ensure_collection()
        self._client.delete_collection(self._collection)
        self._initialized = False
