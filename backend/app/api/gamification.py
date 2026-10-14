from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import current_student, get_current_user
from app.db import get_db
from app.models import (
    Attempt,
    Chapter,
    ExamDate,
    Lesson,
    Material,
    Question,
    Student,
    StudyPlan,
    StudyTimeEvent,
    Subject,
    Topic,
    User,
)
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

    study_seconds = db.scalar(
        select(func.coalesce(func.sum(StudyTimeEvent.duration_seconds), 0)).where(
            StudyTimeEvent.user_id == user.id
        )
    ) or 0
    attempts = list(
        db.execute(
            select(Attempt.created_at, Attempt.is_correct)
            .join(Question, Question.id == Attempt.question_id)
            .join(Lesson, Lesson.id == Question.lesson_id)
            .join(Material, Material.id == Lesson.material_id)
            .where(
                Attempt.student_id == student.id,
                Material.student_id == student.id,
            )
            .order_by(Attempt.created_at)
        )
    )
    trend_by_day: dict[str, list[int]] = {}
    for created_at, is_correct in attempts:
        day = created_at.date().isoformat()
        values = trend_by_day.setdefault(day, [0, 0])
        values[0] += int(is_correct)
        values[1] += 1
    score_trend = [
        {"date": day, "score": round(correct / total, 4), "attempts": total}
        for day, (correct, total) in sorted(trend_by_day.items())[-14:]
    ]

    upcoming_exams = [
        {
            "id": exam.id,
            "title": exam.title,
            "exam_date": exam.exam_date.isoformat(),
        }
        for exam in db.scalars(
            select(ExamDate)
            .where(ExamDate.user_id == user.id, ExamDate.exam_date >= func.current_date())
            .order_by(ExamDate.exam_date)
            .limit(5)
        )
    ]

    subject_rows = db.execute(
        select(Subject.id, Subject.name, Topic.id, Topic.concept_id)
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Topic, Topic.chapter_id == Chapter.id)
        .join(Material, Material.id == Subject.material_id)
        .where(
            Material.student_id == student.id,
            Subject.archived.is_(False),
            Material.archived.is_(False),
        )
    ).all()
    subject_topics: dict[int, dict] = {}
    topic_scores = adaptive.topic_mastery_map(db, student.id)
    for subject_id, subject_name, topic_id, _concept_id in subject_rows:
        record = subject_topics.setdefault(
            subject_id, {"subject": subject_name, "total": 0, "covered": 0, "score": 0.0}
        )
        score = topic_scores.get(topic_id, 0.0)
        record["total"] += 1
        record["covered"] += int(score > 0)
        record["score"] += score
    subject_progress = [
        {
            **values,
            "mastery": round(values["score"] / values["total"], 4),
        }
        for values in subject_topics.values()
    ]

    return DashboardOut(
        streak=StreakOut(**gamification.streak_summary(db, user.id)),
        topics_total=topics_total,
        topics_covered=covered,
        average_mastery=average,
        due_reviews=len(repetition.due_reviews(db, user.id)),
        achievements_unlocked=unlocked,
        achievements_total=len(achievements),
        active_plan=active_plan,
        study_minutes=study_seconds // 60,
        score_trend=score_trend,
        upcoming_exams=upcoming_exams,
        subject_progress=subject_progress,
    )
