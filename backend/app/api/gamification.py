from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, get_current_user
from app.db import get_db
from app.models import Student, StudyPlan, User
from app.schemas import (
    AchievementOut,
    ActivePlanOut,
    DashboardOut,
    StreakOut,
)
from app.services import adaptive, gamification, planner, repetition

router = APIRouter(prefix="/api/gamification", tags=["gamification"])


@router.get("/streak", response_model=StreakOut)
def get_streak(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreakOut:
    return StreakOut(**gamification.streak_summary(db, user.id))


@router.get("/achievements", response_model=list[AchievementOut])
def get_achievements(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AchievementOut]:
    return [
        AchievementOut(
            code=achievement.code,
            name=achievement.name,
            description=achievement.description,
            icon=achievement.icon,
            unlocked=unlocked_at is not None,
            unlocked_at=unlocked_at,
        )
        for achievement, unlocked_at in gamification.user_achievements(db, user.id)
    ]


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardOut:
    mastery = adaptive.topic_mastery_map(db, student.id)
    topics_total = len(mastery)
    covered = sum(1 for score in mastery.values() if score > 0)
    average = round(sum(mastery.values()) / topics_total, 4) if topics_total else 0.0

    achievements = gamification.user_achievements(db, user.id)
    unlocked = sum(1 for _, at in achievements if at is not None)

    active = db.scalar(
        select(StudyPlan).where(
            StudyPlan.user_id == user.id, StudyPlan.status == "active"
        )
    )
    active_plan = None
    if active is not None:
        total, completed, percent = planner.progress(
            planner.plan_items(db, active.id)
        )
        active_plan = ActivePlanOut(
            id=active.id,
            total_items=total,
            completed_items=completed,
            percent_complete=percent,
        )

    return DashboardOut(
        streak=StreakOut(**gamification.streak_summary(db, user.id)),
        topics_total=topics_total,
        topics_covered=covered,
        average_mastery=average,
        due_reviews=len(repetition.due_reviews(db, user.id)),
        achievements_unlocked=unlocked,
        achievements_total=len(achievements),
        active_plan=active_plan,
    )
