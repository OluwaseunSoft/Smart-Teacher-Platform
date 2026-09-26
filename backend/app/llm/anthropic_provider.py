from __future__ import annotations

from app.llm.base import LLMError, LLMProvider, Message

DEFAULT_MODEL = "claude-3-5-sonnet-latest"


class AnthropicProvider(LLMProvider):
    """Generation provider. Anthropic has no first-party embeddings API, so
    `embed` raises — configure EMBEDDING_PROVIDER to openai or ollama."""

    name = "anthropic"

    def __init__(self, api_key: str, model: str = "") -> None:
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is required for the anthropic provider.")
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover
            raise LLMError("anthropic package is not installed.") from exc

        self._client = Anthropic(api_key=api_key)
        self.model = model or DEFAULT_MODEL
        self._model = self.model

    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        self.last_model = self._model
        try:
            resp = self._client.messages.create(
                model=self._model,
                system=system or "",
                messages=messages,  # type: ignore[arg-type]
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"Anthropic completion failed: {exc}") from exc

        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.last_usage = {
                "prompt_tokens": int(getattr(usage, "input_tokens", 0) or 0),
                "completion_tokens": int(getattr(usage, "output_tokens", 0) or 0),
            }

        return "".join(block.text for block in resp.content if block.type == "text")

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise LLMError(
            "Anthropic does not provide embeddings. Set EMBEDDING_PROVIDER "
            "to 'openai' or 'ollama'."
        )
