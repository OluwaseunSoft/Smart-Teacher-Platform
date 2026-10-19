from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.llm.base import LLMOutputTruncated
from app.llm.anthropic_provider import AnthropicProvider, DEFAULT_MODEL


def test_default_model_is_current_sonnet_api_id():
    assert DEFAULT_MODEL == "claude-sonnet-5-5"


def test_complete_omits_unsupported_temperature_argument():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider.model = "claude-test"
    provider._model = "claude-test"
    provider.last_usage = {}

    captured = {}

    def create(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="reply")],
            usage=SimpleNamespace(input_tokens=3, output_tokens=2),
        )

    provider._client = SimpleNamespace(messages=SimpleNamespace(create=create))

    assert provider.complete(
        [{"role": "user", "content": "hello"}], temperature=0.8
    ) == "reply"
    assert captured["max_tokens"] == 2048
    assert "temperature" not in captured
    assert provider.last_usage == {"prompt_tokens": 3, "completion_tokens": 2}


def test_truncated_response_raises_and_preserves_usage():
    provider = AnthropicProvider.__new__(AnthropicProvider)
    provider._model = "claude-test"
    provider._client = SimpleNamespace(messages=SimpleNamespace(
        create=lambda **kwargs: SimpleNamespace(
            content=[SimpleNamespace(type="text", text='{"objectives": ["Learn"]')],
            stop_reason="max_tokens",
            usage=SimpleNamespace(input_tokens=10, output_tokens=4096),
        )
    ))
    with pytest.raises(LLMOutputTruncated, match="4096-token"):
        provider.complete([], max_tokens=4096)
    assert provider.last_usage["completion_tokens"] == 4096
