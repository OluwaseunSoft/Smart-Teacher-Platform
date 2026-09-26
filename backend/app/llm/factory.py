from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.llm.base import LLMError, LLMProvider


def _build(provider: str, *, for_embedding: bool = False) -> LLMProvider:
    provider = provider.lower().strip()

    if provider == "openai":
        from app.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            embed_model=settings.EMBEDDING_MODEL,
        )
    if provider == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        if for_embedding:
            raise LLMError(
                "anthropic cannot be used as EMBEDDING_PROVIDER; use openai or ollama."
            )
        return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY, model=settings.LLM_MODEL)
    if provider == "ollama":
        from app.llm.ollama_provider import OllamaProvider

        return OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.LLM_MODEL,
            embed_model=settings.EMBEDDING_MODEL,
        )

    raise LLMError(f"Unknown provider: {provider!r}")


@lru_cache
def get_llm() -> LLMProvider:
    """Generation provider."""
    return _build(settings.LLM_PROVIDER)


@lru_cache
def get_embedder() -> LLMProvider:
    """Embedding provider (may differ from the generation provider)."""
    return _build(settings.EMBEDDING_PROVIDER, for_embedding=True)
