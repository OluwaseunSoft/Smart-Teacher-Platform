from __future__ import annotations

import httpx

from app.llm.base import LLMError, LLMProvider, Message

DEFAULT_MODEL = "llama3.1"
DEFAULT_EMBED_MODEL = "nomic-embed-text"


class OllamaProvider(LLMProvider):
    """Local, key-free inference via the Ollama HTTP API."""

    name = "ollama"

    def __init__(self, base_url: str, model: str = "", embed_model: str = "") -> None:
        self._base_url = base_url.rstrip("/")
        self.model = model or DEFAULT_MODEL
        self._model = self.model
        self._embed_model = embed_model or DEFAULT_EMBED_MODEL

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        payload: list[Message] = []
        if system:
            payload.append({"role": "system", "content": system})
        payload.extend(messages)

        self.last_model = self._model
        try:
            with httpx.Client(timeout=300) as client:
                resp = client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": payload,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama completion failed: {exc}") from exc

        body = resp.json()
        self.last_usage = {
            "prompt_tokens": int(body.get("prompt_eval_count", 0) or 0),
            "completion_tokens": int(body.get("eval_count", 0) or 0),
        }
        return body.get("message", {}).get("content", "")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self.last_model = self._embed_model
        try:
            with httpx.Client(timeout=300) as client:
                resp = client.post(
                    f"{self._base_url}/api/embed",
                    json={"model": self._embed_model, "input": texts},
                )
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"Ollama embedding failed: {exc}") from exc

        return resp.json().get("embeddings", [])
