from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select

from app.models import Attempt, Mastery, MasteryEvent, Student
from app.seed import seed


def test_seed_populates_mastery_history(db_session):
    result = seed(
        db_session, now=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)
    )

    assert result["created"] is True
    events = db_session.scalar(select(func.count()).select_from(MasteryEvent))
    attempts = db_session.scalar(select(func.count()).select_from(Attempt))
    mastery = db_session.scalar(select(func.count()).select_from(Mastery))

    assert events > 0
    assert events == attempts
    assert mastery > 0
    assert result["mastery_events"] == events


def test_seed_mastery_events_are_ordered_and_linked(db_session):
    seed(db_session, now=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))

    student = db_session.scalar(select(Student))
    events = list(
        db_session.scalars(
            select(MasteryEvent)
            .where(MasteryEvent.student_id == student.id)
            .order_by(MasteryEvent.created_at, MasteryEvent.id)
        )
    )

    assert events
    assert all(event.topic_id is not None for event in events)
    assert all(event.source == "quiz" for event in events)
    assert {event.is_correct for event in events} == {True, False}


def test_seed_is_idempotent(db_session):
    first = seed(
        db_session, now=datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)
    )
    second = seed(
        db_session, now=datetime(2026, 9, 26, 12, 0, tzinfo=timezone.utc)
    )

    assert first["created"] is True
    assert second["created"] is False
