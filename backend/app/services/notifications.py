"""In-app notifications: reminders for due reviews and today's plan tasks.

Reminders are generated idempotently — at most one of each type per user per day.
See `docs/06-v2-requirements.md` feature K.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Achievement,
    Notification,
    StudyPlan,
    StudyPlanItem,
)
from app.services import repetition

TYPE_REVIEW_DUE = "review_due"
TYPE_PLAN_TASK = "plan_task"
TYPE_ACHIEVEMENT = "achievement"


def create(
    db: Session,
    user_id: int,
    *,
    type: str,
    title: str,
    body: str = "",
) -> Notification:
    notification = Notification(
        user_id=user_id, type=type, title=title[:200], body=body
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def list_notifications(
    db: Session, user_id: int, *, unread_only: bool = False, limit: int = 50
) -> list[Notification]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
    stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def unread_count(db: Session, user_id: int) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
        )
        or 0
    )


def get_notification(
    db: Session, user_id: int, notification_id: int
) -> Notification | None:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user_id:
        return None
    return notification


def mark_read(
    db: Session, notification: Notification, *, now: datetime | None = None
) -> Notification:
    if notification.read_at is None:
        notification.read_at = now or datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_read(
    db: Session, user_id: int, *, now: datetime | None = None
) -> int:
    now = now or datetime.now(timezone.utc)
    updated = 0
    for notification in db.scalars(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    ):
        notification.read_at = now
        updated += 1
    if updated:
        db.commit()
    return updated


def generate_reminders(
    db: Session, user_id: int, *, today: date | None = None
) -> list[Notification]:
    """Create today's review/plan reminders if not already present."""
    today = today or datetime.now(timezone.utc).date()
    created: list[Notification] = []

    due = repetition.due_reviews(db, user_id)
    if due and not _exists_today(db, user_id, TYPE_REVIEW_DUE, today):
        created.append(
            create(
                db,
                user_id,
                type=TYPE_REVIEW_DUE,
                title=f"{len(due)} topic(s) due for review",
                body="Spaced repetition is most effective when reviews are on time.",
            )
        )

    pending = _pending_plan_items_today(db, user_id, today)
    if pending and not _exists_today(db, user_id, TYPE_PLAN_TASK, today):
        created.append(
            create(
                db,
                user_id,
                type=TYPE_PLAN_TASK,
                title=f"{pending} study task(s) planned today",
                body="Stay on track with your study plan.",
            )
        )

    return created


def notify_unlocked(
    db: Session, user_id: int, achievements: list[Achievement]
) -> list[Notification]:
    created = []
    for achievement in achievements:
        created.append(
            create(
                db,
                user_id,
                type=TYPE_ACHIEVEMENT,
                title=f"Achievement unlocked: {achievement.name}",
                body=achievement.description,
            )
        )
    return created


def _exists_today(
    db: Session, user_id: int, type: str, today: date
) -> bool:
    start = datetime.combine(today, time.min)
    existing = db.scalar(
        select(Notification.id).where(
            Notification.user_id == user_id,
            Notification.type == type,
            Notification.created_at >= start,
        )
    )
    return existing is not None


def _pending_plan_items_today(db: Session, user_id: int, today: date) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(StudyPlanItem)
            .join(StudyPlan, StudyPlan.id == StudyPlanItem.plan_id)
            .where(
                StudyPlan.user_id == user_id,
                StudyPlan.status == "active",
                StudyPlanItem.status == "pending",
                StudyPlanItem.scheduled_for <= today,
            )
        )
        or 0
    )
