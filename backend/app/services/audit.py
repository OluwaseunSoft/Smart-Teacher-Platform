from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import AuditLog


def record_audit(
    db: Session,
    *,
    actor_user_id: int | None,
    action: str,
    target_type: str = "",
    target_id: str | int = "",
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        meta=meta or {},
    )
    db.add(entry)
    return entry
