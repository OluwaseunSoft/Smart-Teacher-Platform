from __future__ import annotations

from app.llm.base import LLMError, LLMProvider, Message

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_EMBED_MODEL = "text-embedding-3-small"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str = "", embed_model: str = "") -> None:
        if not api_key:
            raise LLMError("OPENAI_API_KEY is required for the openai provider.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise LLMError("openai package is not installed.") from exc

        self._client = OpenAI(api_key=api_key)
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
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=payload,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"OpenAI completion failed: {exc}") from exc

        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.last_usage = {
                "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
                "completion_tokens": int(
                    getattr(usage, "completion_tokens", 0) or 0
                ),
            }

        return resp.choices[0].message.content or ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        self.last_model = self._embed_model
        try:
            resp = self._client.embeddings.create(
                model=self._embed_model, input=texts
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"OpenAI embedding failed: {exc}") from exc

        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.last_usage = {
                "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
                "completion_tokens": 0,
            }

        return [item.embedding for item in resp.data]
