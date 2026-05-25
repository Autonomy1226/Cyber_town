from dataclasses import dataclass
import httpx


@dataclass
class LLMConfig:
    base_url: str = "https://api.deepseek.com/v1"
    api_key: str = ""
    model: str = "deepseek-chat"
    embedding_model: str = ""
    temperature: float = 0.8
    max_tokens: int = 512
    timeout_seconds: float = 30.0


class LLMClient:
    """Async OpenAI-compatible client for chat completions and embeddings."""

    def __init__(self, config: LLMConfig):
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout_seconds,
        )

    async def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self._config.model,
            "messages": messages,
            "temperature": self._config.temperature,
            "max_tokens": self._config.max_tokens,
        }
        resp = await self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    async def get_embedding(self, text: str) -> list[float]:
        if not self._config.embedding_model:
            return []
        payload = {
            "model": self._config.embedding_model,
            "input": text,
        }
        resp = await self._client.post("/embeddings", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]

    async def close(self) -> None:
        await self._client.aclose()
