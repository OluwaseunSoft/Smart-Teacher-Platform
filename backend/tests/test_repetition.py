from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services import repetition


def _now() -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_sm2_intervals_grow_on_success(db_session):
    now = _now()
    schedule = repetition.get_or_create_schedule(db_session, 1, 10, now=now)
    assert schedule.interval_days == 0
    assert schedule.repetitions == 0

    repetition.apply_review(schedule, 5, now=now)
    assert schedule.interval_days == 1
    assert schedule.repetitions == 1

    repetition.apply_review(schedule, 5, now=now + timedelta(days=1))
    assert schedule.interval_days == 6
    assert schedule.repetitions == 2

    repetition.apply_review(schedule, 5, now=now + timedelta(days=7))
    assert schedule.interval_days == 16  # round(6 * 2.7)
    assert schedule.repetitions == 3
    assert schedule.ease == 2.8


def test_sm2_lapse_resets_repetitions(db_session):
    now = _now()
    schedule = repetition.get_or_create_schedule(db_session, 1, 10, now=now)
    repetition.apply_review(schedule, 5, now=now)
    repetition.apply_review(schedule, 5, now=now)
    assert schedule.repetitions == 2

    repetition.apply_review(schedule, 1, now=now + timedelta(days=2))
    assert schedule.repetitions == 0
    assert schedule.lapses == 1
    assert schedule.interval_days == 1
    assert schedule.ease == 2.5  # 2.7 - 0.2


def test_record_review_is_idempotent_per_topic(db_session):
    now = _now()
    repetition.record_review(db_session, 1, 10, 4, now=now)
    repetition.record_review(db_session, 1, 10, 4, now=now + timedelta(days=1))
    schedule = repetition.get_or_create_schedule(db_session, 1, 10, now=now)
    assert schedule.repetitions == 2
    assert schedule.last_reviewed_at is not None


def test_due_reviews_filters_future(db_session):
    now = _now()
    repetition.get_or_create_schedule(db_session, 1, 1, now=now - timedelta(days=2))
    repetition.get_or_create_schedule(db_session, 1, 2, now=now + timedelta(days=2))
    db_session.commit()

    due = repetition.due_reviews(db_session, 1, now=now)
    assert [s.topic_id for s in due] == [1]
    assert repetition.is_due(due[0], now=now) is True


def test_review_strength_and_quality_mapping(db_session):
    assert repetition.review_strength(None) == 0.0

    now = _now()
    schedule = repetition.get_or_create_schedule(db_session, 1, 10, now=now)
    assert repetition.review_strength(schedule) == 0.0

    repetition.apply_review(schedule, 5, now=now)
    # interval 1 day -> 1/30, no lapses.
    assert repetition.review_strength(schedule) == round(1 / 30, 4)

    assert repetition.quality_from_score(0.95) == 5
    assert repetition.quality_from_score(0.75) == 4
    assert repetition.quality_from_score(0.55) == 3
    assert repetition.quality_from_score(0.35) == 2
    assert repetition.quality_from_score(0.1) == 1
    assert repetition.clamp_quality(9) == 5
    assert repetition.clamp_quality(-3) == 0
