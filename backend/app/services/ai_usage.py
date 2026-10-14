from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy.orm import Session

from app.models import AIUsageLog

_TOKEN_RATES_PER_MILLION: tuple[tuple[str, float, float], ...] = (
    ("gpt-4o-mini", 0.15, 0.60),
    ("gpt-4o", 2.50, 10.00),
    ("gpt-4.1-mini", 0.40, 1.60),
    ("gpt-4.1", 2.00, 8.00),
    ("claude-3-5-haiku", 0.80, 4.00),
    ("claude-3-5-sonnet", 3.00, 15.00),
    ("claude-3-7-sonnet", 3.00, 15.00),
)


def estimate_cost_usd(
    provider: str, model: str, prompt: int, completion: int
) -> float | None:
    """Estimate hosted-provider token spend; local providers are reported as zero."""
    if provider.lower() in {"ollama", "local"}:
        return 0.0
    normalized = model.lower()
    for model_prefix, input_rate, output_rate in _TOKEN_RATES_PER_MILLION:
        if model_prefix in normalized:
            return round(
                (prompt * input_rate + completion * output_rate) / 1_000_000,
                8,
            )
    return None


@contextmanager
def track_ai(
    db: Session,
    provider: Any,
    operation: str,
    *,
    user_id: int | None = None,
    commit: bool = False,
) -> Iterator[None]:
    """Record one provider call in ``ai_usage_logs``.

    The row is added to the *caller's* session (never an independent one) so tests
    stay isolated. It is persisted by the caller's next commit; on error it is
    committed here because the caller is almost always about to abort. Set
    ``commit=True`` for call sites that do not otherwise commit afterwards.

    Logging is best-effort: a failure to record usage never masks the provider
    result or exception.
    """
    start = time.perf_counter()
    status = "ok"
    error: str | None = None
    try:
        yield
    except Exception as exc:  # noqa: BLE001
        status = "error"
        error = str(exc)[:500]
        raise
    finally:
        usage = getattr(provider, "last_usage", None) or {}
        model = getattr(provider, "last_model", "") or getattr(provider, "model", "")
        entry = AIUsageLog(
            user_id=user_id,
            provider=str(getattr(provider, "name", "") or "")[:40],
            model=str(model or "")[:80],
            operation=operation[:80],
            prompt_tokens=int(usage.get("prompt_tokens", 0) or 0),
            completion_tokens=int(usage.get("completion_tokens", 0) or 0),
            cost_usd=estimate_cost_usd(
                str(getattr(provider, "name", "") or ""),
                str(model or ""),
                int(usage.get("prompt_tokens", 0) or 0),
                int(usage.get("completion_tokens", 0) or 0),
            ),
            latency_ms=int((time.perf_counter() - start) * 1000),
            status=status,
            error=error,
        )
        try:
            db.add(entry)
            if commit or status == "error":
                db.commit()
        except Exception:  # noqa: BLE001
            db.rollback()
