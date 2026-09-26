"""Provider-agnostic LLM interface.

Services depend only on this module, never on a specific SDK.
Calls are synchronous to match the synchronous SQLAlchemy session model. An async
variant can be introduced later for streaming without changing service call sites.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

Message = dict[str, str]

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class LLMError(RuntimeError):
    """Raised when a provider call fails. Routes translate this to HTTP 502."""


def _extract_json(text: str) -> Any:
    """Best-effort extraction of the first JSON value from model output."""
    text = text.strip()

    fenced = _JSON_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        end = text.rfind(closer)
        if start != -1 and end != -1 and end > start:
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise LLMError(f"Model did not return valid JSON: {text[:200]!r}")


class LLMProvider(ABC):
    name: str = "base"
    model: str = ""
    # Updated after each call; used by the AI-usage logger. Never mutated in place.
    last_usage: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0}
    # Model actually used by the last call (embedding model for ``embed``).
    last_model: str = ""

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        """Return a plain-text completion."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text."""

    def generate_json(
        self,
        messages: list[Message],
        *,
        system: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 4096,
    ) -> Any:
        """Completion constrained to JSON, with a single repair retry."""
        base_system = (system or "").strip()
        json_system = (
            base_system
            + "\n\nYou must respond with valid JSON only. "
            "Do not include markdown fences or commentary."
        ).strip()

        raw = self.complete(
            messages, system=json_system, temperature=temperature, max_tokens=max_tokens
        )
        try:
            return _extract_json(raw)
        except LLMError:
            repair = messages + [
                {"role": "assistant", "content": raw},
                {
                    "role": "user",
                    "content": "That was not valid JSON. Return ONLY the JSON value.",
                },
            ]
            retry = self.complete(
                repair, system=json_system, temperature=0.0, max_tokens=max_tokens
            )
            return _extract_json(retry)
