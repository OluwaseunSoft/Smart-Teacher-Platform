from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_topic
from app.db import get_db
from app.models import ReviewSchedule, Student, Topic
from app.schemas import (
    ReviewQueueOut,
    ReviewScheduleOut,
    ReviewSubmitIn,
    ReviewSummaryOut,
)
from app.services import adaptive, gamification, notifications, repetition

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def _out(schedule: ReviewSchedule, topic: Topic | None, mastery: float) -> ReviewScheduleOut:
    return ReviewScheduleOut(
        topic_id=schedule.topic_id,
        topic_title=topic.title if topic is not None else "",
        interval_days=schedule.interval_days,
        ease=round(schedule.ease, 4),
        repetitions=schedule.repetitions,
        lapses=schedule.lapses,
        due_at=schedule.due_at,
        last_reviewed_at=schedule.last_reviewed_at,
        is_due=repetition.is_due(schedule),
        mastery=round(mastery, 4),
        retention=repetition.review_strength(schedule),
    )


def _topics(db: Session, topic_ids: list[int]) -> dict[int, Topic]:
    if not topic_ids:
        return {}
    return {
        topic.id: topic
        for topic in db.scalars(select(Topic).where(Topic.id.in_(topic_ids)))
    }


@router.get("/summary", response_model=ReviewSummaryOut)
def review_summary(
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> ReviewSummaryOut:
    if student.user_id is None:
        return ReviewSummaryOut(due_count=0, scheduled_count=0, reviewed_count=0)

    schedules = list(
        db.scalars(
            select(ReviewSchedule).where(ReviewSchedule.user_id == student.user_id)
        )
    )
    now = repetition.utcnow()
    return ReviewSummaryOut(
        due_count=sum(1 for s in schedules if repetition.is_due(s, now=now)),
        scheduled_count=len(schedules),
        reviewed_count=sum(1 for s in schedules if s.last_reviewed_at is not None),
    )


@router.get("/queue", response_model=ReviewQueueOut)
def review_queue(
    limit: int = Query(default=20, ge=1, le=100),
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> ReviewQueueOut:
    if student.user_id is None:
        return ReviewQueueOut(items=[], total=0)

    schedules = repetition.due_reviews(db, student.user_id, limit=limit)
    return _enrich(db, student, schedules)


@router.get("", response_model=ReviewQueueOut)
def list_reviews(
    due_only: bool = False,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> ReviewQueueOut:
    if student.user_id is None:
        return ReviewQueueOut(items=[], total=0)

    schedules = list(
        db.scalars(
            select(ReviewSchedule)
            .where(ReviewSchedule.user_id == student.user_id)
            .order_by(ReviewSchedule.due_at.asc())
        )
    )
    if due_only:
        now = repetition.utcnow()
        schedules = [s for s in schedules if repetition.is_due(s, now=now)]
    return _enrich(db, student, schedules)


@router.post("/{topic_id}", response_model=ReviewScheduleOut)
def submit_review(
    topic_id: int,
    payload: ReviewSubmitIn,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> ReviewScheduleOut:
    topic = owned_topic(db, topic_id, student)
    if student.user_id is None:
        # A student without a linked user cannot own review schedules.
        raise HTTPException(status_code=404, detail="Topic not found")

    schedule = repetition.record_review(db, student.user_id, topic_id, payload.quality)
    unlocked = gamification.record_and_evaluate(db, student.user_id)
    notifications.notify_unlocked(db, student.user_id, unlocked)
    return _out(schedule, topic, adaptive.topic_mastery(db, student.id, topic_id))


def _enrich(
    db: Session, student: Student, schedules: list[ReviewSchedule]
) -> ReviewQueueOut:
    topics = _topics(db, [s.topic_id for s in schedules])
    mastery = adaptive.topic_mastery_map(db, student.id)
    items = [
        _out(s, topics.get(s.topic_id), mastery.get(s.topic_id, 0.0))
        for s in schedules
    ]
    return ReviewQueueOut(items=items, total=len(items))
