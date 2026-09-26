"""Study planner: exam dates, deterministic plan generation and progress.

No LLM is involved. Topics for the student's materials are distributed across the
days leading up to an exam, weakest topics first, respecting a daily study budget.
See `docs/06-v2-requirements.md` feature I.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Chapter,
    ExamDate,
    Material,
    StudyPlan,
    StudyPlanItem,
    Subject,
    Topic,
)

DIFFICULTY_MINUTES = {"intro": 20, "core": 30, "advanced": 45}
DEFAULT_MINUTES = 30
DEFAULT_DAILY_MINUTES = 60
MIN_DAILY_MINUTES = 15
MAX_DAILY_MINUTES = 480

STATUS_PENDING = "pending"
STATUS_DONE = "done"


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def estimated_minutes(topic: Topic) -> int:
    return DIFFICULTY_MINUTES.get(topic.difficulty, DEFAULT_MINUTES)


# ---- Exam dates -------------------------------------------------------------
def create_exam(
    db: Session,
    user_id: int,
    *,
    title: str,
    exam_date: date,
    subject_id: int | None = None,
) -> ExamDate:
    exam = ExamDate(
        user_id=user_id,
        subject_id=subject_id,
        title=title[:200],
        exam_date=exam_date,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def list_exams(db: Session, user_id: int) -> list[ExamDate]:
    return list(
        db.scalars(
            select(ExamDate)
            .where(ExamDate.user_id == user_id)
            .order_by(ExamDate.exam_date.asc(), ExamDate.id.asc())
        )
    )


def get_exam(db: Session, user_id: int, exam_id: int) -> ExamDate | None:
    exam = db.get(ExamDate, exam_id)
    if exam is None or exam.user_id != user_id:
        return None
    return exam


def delete_exam(db: Session, exam: ExamDate) -> None:
    for plan in db.scalars(
        select(StudyPlan).where(StudyPlan.exam_date_id == exam.id)
    ):
        db.delete(plan)
    db.delete(exam)
    db.commit()


# ---- Plan generation --------------------------------------------------------
def ordered_topics(
    db: Session,
    student_id: int,
    *,
    subject_id: int | None = None,
    mastery: dict[int, float] | None = None,
) -> list[Topic]:
    """Student's topics, weakest first, then curriculum order."""
    mastery = mastery or {}
    stmt = (
        select(Topic)
        .join(Chapter, Chapter.id == Topic.chapter_id)
        .join(Subject, Subject.id == Chapter.subject_id)
        .join(Material, Material.id == Subject.material_id)
        .where(Material.student_id == student_id)
    )
    if subject_id is not None:
        stmt = stmt.where(Subject.id == subject_id)

    topics = list(db.scalars(stmt))
    return sorted(
        topics,
        key=lambda t: (
            round(mastery.get(t.id, 0.0), 4),
            _subject_order(t),
            _chapter_order(t),
            t.order_index,
            t.id,
        ),
    )


def generate_plan(
    db: Session,
    user_id: int,
    student_id: int,
    exam: ExamDate,
    *,
    daily_minutes: int = DEFAULT_DAILY_MINUTES,
    subject_id: int | None = None,
    mastery: dict[int, float] | None = None,
) -> StudyPlan:
    daily_minutes = max(MIN_DAILY_MINUTES, min(MAX_DAILY_MINUTES, daily_minutes))
    topics = ordered_topics(
        db, student_id, subject_id=subject_id, mastery=mastery
    )

    # Archive any currently active plan for this user before generating a new one.
    for existing in db.scalars(
        select(StudyPlan).where(
            StudyPlan.user_id == user_id, StudyPlan.status == "active"
        )
    ):
        existing.status = "archived"

    plan = StudyPlan(user_id=user_id, exam_date_id=exam.id, status="active")
    db.add(plan)
    db.flush()

    start = today_utc()
    last_day = max(start, exam.exam_date - timedelta(days=1))
    day_offset = 0
    used_today = 0

    for topic in topics:
        minutes = estimated_minutes(topic)
        over_budget = used_today + minutes > daily_minutes
        if used_today and over_budget:
            day_offset += 1
            used_today = 0
        scheduled = start + timedelta(days=day_offset)
        if scheduled > last_day:
            scheduled = last_day
        db.add(
            StudyPlanItem(
                plan_id=plan.id,
                topic_id=topic.id,
                scheduled_for=scheduled,
                estimated_minutes=minutes,
                status=STATUS_PENDING,
            )
        )
        used_today += minutes

    db.commit()
    db.refresh(plan)
    return plan


def list_plans(db: Session, user_id: int) -> list[StudyPlan]:
    return list(
        db.scalars(
            select(StudyPlan)
            .where(StudyPlan.user_id == user_id)
            .order_by(StudyPlan.created_at.desc(), StudyPlan.id.desc())
        )
    )


def get_plan(db: Session, user_id: int, plan_id: int) -> StudyPlan | None:
    plan = db.get(StudyPlan, plan_id)
    if plan is None or plan.user_id != user_id:
        return None
    return plan


def plan_items(db: Session, plan_id: int) -> list[StudyPlanItem]:
    return list(
        db.scalars(
            select(StudyPlanItem)
            .where(StudyPlanItem.plan_id == plan_id)
            .order_by(
                StudyPlanItem.scheduled_for.asc(), StudyPlanItem.id.asc()
            )
        )
    )


def set_item_status(
    db: Session,
    item: StudyPlanItem,
    status: str,
    *,
    now: datetime | None = None,
) -> StudyPlanItem:
    now = now or datetime.now(timezone.utc)
    item.status = status
    item.completed_at = now if status == STATUS_DONE else None
    db.commit()
    db.refresh(item)
    return item


def delete_plan(db: Session, plan: StudyPlan) -> None:
    db.delete(plan)
    db.commit()


def progress(items: list[StudyPlanItem]) -> tuple[int, int, float]:
    total = len(items)
    completed = sum(1 for item in items if item.status == STATUS_DONE)
    percent = round(completed / total, 4) if total else 0.0
    return total, completed, percent


def _subject_order(topic: Topic) -> int:
    subject = topic.chapter.subject if topic.chapter is not None else None
    return subject.order_index if subject is not None else 0


def _chapter_order(topic: Topic) -> int:
    return topic.chapter.order_index if topic.chapter is not None else 0
