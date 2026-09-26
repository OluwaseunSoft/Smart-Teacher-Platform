"""SM-2-like spaced repetition scheduling for topics.

Pure, deterministic and testable: given a recall `quality` (0-5), update a
`ReviewSchedule`'s interval, ease, repetition count and next due date. No LLM is
involved. See `docs/06-v2-requirements.md` feature H and `docs/02-data-model.md`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReviewSchedule

DEFAULT_EASE = 2.5
MIN_EASE = 1.3
MAX_EASE = 2.8
PASS_QUALITY = 3
MAX_INTERVAL_DAYS = 365


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _naive_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; normalise so comparisons never raise."""
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def clamp_quality(value: int) -> int:
    return max(0, min(5, int(value)))


def get_or_create_schedule(
    db: Session, user_id: int, topic_id: int, *, now: datetime | None = None
) -> ReviewSchedule:
    schedule = db.scalar(
        select(ReviewSchedule).where(
            ReviewSchedule.user_id == user_id, ReviewSchedule.topic_id == topic_id
        )
    )
    if schedule is not None:
        return schedule

    schedule = ReviewSchedule(
        user_id=user_id,
        topic_id=topic_id,
        interval_days=0,
        ease=DEFAULT_EASE,
        repetitions=0,
        lapses=0,
        due_at=now or utcnow(),
    )
    db.add(schedule)
    db.flush()
    return schedule


def apply_review(
    schedule: ReviewSchedule, quality: int, *, now: datetime | None = None
) -> ReviewSchedule:
    """Update `schedule` in place using the SM-2 rule and return it."""
    now = now or utcnow()
    quality = clamp_quality(quality)

    if quality < PASS_QUALITY:
        schedule.repetitions = 0
        schedule.lapses += 1
        schedule.interval_days = 1
        schedule.ease = max(MIN_EASE, schedule.ease - 0.2)
    else:
        if schedule.repetitions == 0:
            schedule.interval_days = 1
        elif schedule.repetitions == 1:
            schedule.interval_days = 6
        else:
            schedule.interval_days = min(
                MAX_INTERVAL_DAYS, round(schedule.interval_days * schedule.ease)
            )
        schedule.repetitions += 1
        adjustment = 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        schedule.ease = min(MAX_EASE, max(MIN_EASE, schedule.ease + adjustment))

    schedule.last_reviewed_at = now
    schedule.due_at = now + timedelta(days=schedule.interval_days)
    return schedule


def record_review(
    db: Session,
    user_id: int,
    topic_id: int,
    quality: int,
    *,
    now: datetime | None = None,
) -> ReviewSchedule:
    now = now or utcnow()
    schedule = get_or_create_schedule(db, user_id, topic_id, now=now)
    apply_review(schedule, quality, now=now)
    db.commit()
    db.refresh(schedule)
    return schedule


def due_reviews(
    db: Session, user_id: int, *, now: datetime | None = None, limit: int | None = None
) -> list[ReviewSchedule]:
    now = now or utcnow()
    stmt = (
        select(ReviewSchedule)
        .where(
            ReviewSchedule.user_id == user_id,
            (ReviewSchedule.due_at.is_(None))
            | (ReviewSchedule.due_at <= _naive_utc(now)),
        )
        .order_by(ReviewSchedule.due_at.asc())
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def is_due(schedule: ReviewSchedule, *, now: datetime | None = None) -> bool:
    if schedule.due_at is None:
        return True
    return _naive_utc(schedule.due_at) <= _naive_utc(now or utcnow())


def review_strength(schedule: ReviewSchedule | None) -> float:
    """A 0-1 measure of retention: long intervals help, lapses hurt."""
    if schedule is None or schedule.repetitions <= 0:
        return 0.0
    interval_component = min(1.0, schedule.interval_days / 30.0)
    lapse_penalty = min(0.5, 0.1 * schedule.lapses)
    return round(max(0.0, min(1.0, interval_component - lapse_penalty)), 4)


def quality_from_score(score: float) -> int:
    """Map a 0-1 assessment score onto an SM-2 quality grade."""
    if score >= 0.9:
        return 5
    if score >= 0.7:
        return 4
    if score >= 0.5:
        return 3
    if score >= 0.3:
        return 2
    return 1
