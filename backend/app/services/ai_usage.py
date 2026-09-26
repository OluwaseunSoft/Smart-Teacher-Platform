from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy.orm import Session

from app.models import AIUsageLog


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
