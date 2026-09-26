"""Gamification: daily streaks, achievements and progress statistics.

Deterministic and LLM-free. ``record_activity`` is called from activity endpoints
(quizzes, reviews, tutor, planner) to advance the streak, and ``evaluate`` unlocks
any achievements whose criteria the student now meets. See
`docs/06-v2-requirements.md` feature J.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Achievement,
    Attempt,
    Mastery,
    ReviewSchedule,
    Student,
    StudentProfile,
    Streak,
    TutorConversation,
    UserAchievement,
)

DEFAULT_ACHIEVEMENTS: list[dict] = [
    {
        "code": "first_steps",
        "name": "First Steps",
        "description": "Answer your first practice question.",
        "icon": "footprints",
        "criteria": {"attempts": 1},
    },
    {
        "code": "quiz_ace",
        "name": "Perfect Score",
        "description": "Ace a quiz with a perfect score.",
        "icon": "star",
        "criteria": {"quiz_score": 1.0},
    },
    {
        "code": "streak_3",
        "name": "On a Roll",
        "description": "Study three days in a row.",
        "icon": "flame",
        "criteria": {"streak": 3},
    },
    {
        "code": "streak_7",
        "name": "Unstoppable",
        "description": "Study seven days in a row.",
        "icon": "fire",
        "criteria": {"streak": 7},
    },
    {
        "code": "review_10",
        "name": "Reviewer",
        "description": "Complete ten spaced-repetition reviews.",
        "icon": "repeat",
        "criteria": {"reviews": 10},
    },
    {
        "code": "topic_mastered",
        "name": "Topic Master",
        "description": "Reach 80% mastery in a topic.",
        "icon": "brain",
        "criteria": {"topic_mastery": 0.8},
    },
    {
        "code": "first_tutor",
        "name": "Curious Mind",
        "description": "Start a conversation with the tutor.",
        "icon": "message-circle",
        "criteria": {"conversations": 1},
    },
]


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def ensure_achievements(db: Session) -> None:
    existing = {code for code in db.scalars(select(Achievement.code))}
    changed = False
    for spec in DEFAULT_ACHIEVEMENTS:
        if spec["code"] in existing:
            continue
        db.add(
            Achievement(
                code=spec["code"],
                name=spec["name"],
                description=spec["description"],
                icon=spec["icon"],
                criteria=spec["criteria"],
            )
        )
        changed = True
    if changed:
        db.commit()


def get_profile(db: Session, user_id: int) -> StudentProfile:
    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


def record_activity(
    db: Session, user_id: int, *, when: date | None = None
) -> tuple[Streak, StudentProfile]:
    """Register one activity today and advance the daily streak."""
    day = when or today_utc()

    streak = db.scalar(
        select(Streak).where(Streak.user_id == user_id, Streak.date == day)
    )
    if streak is None:
        streak = Streak(user_id=user_id, date=day, activity_count=0)
        db.add(streak)
    streak.activity_count += 1

    profile = get_profile(db, user_id)
    last = profile.last_active_date
    if last != day:
        if last is not None and (day - last).days == 1:
            profile.streak_current += 1
        else:
            profile.streak_current = 1
        profile.streak_longest = max(profile.streak_longest, profile.streak_current)
        profile.last_active_date = day

    db.commit()
    db.refresh(streak)
    db.refresh(profile)
    return streak, profile


def compute_stats(
    db: Session, user_id: int, *, context: dict | None = None
) -> dict[str, float]:
    student = db.scalar(select(Student).where(Student.user_id == user_id))
    student_id = student.id if student is not None else -1

    attempts = db.scalar(
        select(func.count()).select_from(Attempt).where(
            Attempt.student_id == student_id
        )
    )
    max_mastery = db.scalar(
        select(func.max(Mastery.score)).where(Mastery.student_id == student_id)
    )
    reviews = db.scalar(
        select(func.count())
        .select_from(ReviewSchedule)
        .where(
            ReviewSchedule.user_id == user_id,
            ReviewSchedule.last_reviewed_at.is_not(None),
        )
    )
    conversations = db.scalar(
        select(func.count())
        .select_from(TutorConversation)
        .where(TutorConversation.user_id == user_id)
    )
    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )

    stats: dict[str, float] = {
        "attempts": float(attempts or 0),
        "streak": float(profile.streak_current if profile else 0),
        "reviews": float(reviews or 0),
        "topic_mastery": float(max_mastery or 0.0),
        "conversations": float(conversations or 0),
    }
    if context:
        stats.update({k: float(v) for k, v in context.items()})
    return stats


def evaluate(
    db: Session, user_id: int, *, context: dict | None = None
) -> list[Achievement]:
    """Unlock any achievements the student now qualifies for."""
    ensure_achievements(db)
    stats = compute_stats(db, user_id, context=context)

    unlocked_codes = {
        code
        for code in db.scalars(
            select(Achievement.code)
            .join(
                UserAchievement,
                UserAchievement.achievement_id == Achievement.id,
            )
            .where(UserAchievement.user_id == user_id)
        )
    }

    newly_unlocked: list[Achievement] = []
    for achievement in db.scalars(select(Achievement).order_by(Achievement.id)):
        if achievement.code in unlocked_codes:
            continue
        criteria = achievement.criteria or {}
        if not criteria:
            continue
        if all(stats.get(key, 0.0) >= value for key, value in criteria.items()):
            db.add(
                UserAchievement(
                    user_id=user_id, achievement_id=achievement.id
                )
            )
            newly_unlocked.append(achievement)

    if newly_unlocked:
        db.commit()
    return newly_unlocked


def record_and_evaluate(
    db: Session, user_id: int, *, context: dict | None = None
) -> list[Achievement]:
    """Record one activity, then unlock any newly-earned achievements."""
    record_activity(db, user_id)
    return evaluate(db, user_id, context=context)


def user_achievements(
    db: Session, user_id: int
) -> list[tuple[Achievement, datetime | None]]:
    ensure_achievements(db)
    unlocked = {
        row.achievement_id: row.unlocked_at
        for row in db.scalars(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
    }
    return [
        (achievement, unlocked.get(achievement.id))
        for achievement in db.scalars(select(Achievement).order_by(Achievement.id))
    ]


def streak_summary(db: Session, user_id: int) -> dict:
    profile = db.scalar(
        select(StudentProfile).where(StudentProfile.user_id == user_id)
    )
    today = db.scalar(
        select(Streak).where(
            Streak.user_id == user_id, Streak.date == today_utc()
        )
    )
    return {
        "current": profile.streak_current if profile else 0,
        "longest": profile.streak_longest if profile else 0,
        "today_count": today.activity_count if today else 0,
        "last_active_date": profile.last_active_date if profile else None,
    }
