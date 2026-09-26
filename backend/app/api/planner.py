from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, get_current_user
from app.db import get_db
from app.models import ExamDate, StudyPlan, StudyPlanItem, Student, Topic, User
from app.schemas import (
    ExamDateCreateIn,
    ExamDateOut,
    PlanDetailOut,
    PlanGenerateIn,
    PlanItemOut,
    PlanItemUpdateIn,
    PlanOut,
    PlanSummaryOut,
)
from app.services import adaptive, gamification, planner

router = APIRouter(prefix="/api/planner", tags=["planner"])


def _topic_titles(db: Session, items: list[StudyPlanItem]) -> dict[int, str]:
    ids = [item.topic_id for item in items if item.topic_id is not None]
    if not ids:
        return {}
    return {
        topic.id: topic.title
        for topic in db.scalars(select(Topic).where(Topic.id.in_(ids)))
    }


def _item_out(item: StudyPlanItem, titles: dict[int, str]) -> PlanItemOut:
    return PlanItemOut(
        id=item.id,
        topic_id=item.topic_id,
        topic_title=titles.get(item.topic_id, "") if item.topic_id else "",
        scheduled_for=item.scheduled_for,
        estimated_minutes=item.estimated_minutes,
        status=item.status,
        completed_at=item.completed_at,
    )


def _exam_ref(db: Session, plan: StudyPlan) -> ExamDate | None:
    return db.get(ExamDate, plan.exam_date_id) if plan.exam_date_id else None


def _summary(
    db: Session, plan: StudyPlan, items: list[StudyPlanItem] | None = None
) -> PlanSummaryOut:
    items = items if items is not None else planner.plan_items(db, plan.id)
    total, completed, percent = planner.progress(items)
    exam = _exam_ref(db, plan)
    return PlanSummaryOut(
        id=plan.id,
        exam_date_id=plan.exam_date_id,
        status=plan.status,
        created_at=plan.created_at,
        exam_title=exam.title if exam is not None else "",
        exam_date=exam.exam_date if exam is not None else None,
        total_items=total,
        completed_items=completed,
        percent_complete=percent,
    )


def _detail(db: Session, plan: StudyPlan) -> PlanDetailOut:
    items = planner.plan_items(db, plan.id)
    titles = _topic_titles(db, items)
    base = _summary(db, plan, items)
    return PlanDetailOut(
        **base.model_dump(),
        items=[_item_out(item, titles) for item in items],
    )


def _get_plan(db: Session, user: User, plan_id: int) -> StudyPlan:
    plan = planner.get_plan(db, user.id, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post(
    "/exams", response_model=ExamDateOut, status_code=status.HTTP_201_CREATED
)
def create_exam(
    payload: ExamDateCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> planner.ExamDate:
    return planner.create_exam(
        db,
        user.id,
        title=payload.title,
        exam_date=payload.exam_date,
        subject_id=payload.subject_id,
    )


@router.get("/exams", response_model=list[ExamDateOut])
def list_exams(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[planner.ExamDate]:
    return planner.list_exams(db, user.id)


@router.delete("/exams/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    exam = planner.get_exam(db, user.id, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    planner.delete_exam(db, exam)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/plans", response_model=PlanOut, status_code=status.HTTP_201_CREATED
)
def generate_plan(
    payload: PlanGenerateIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudyPlan:
    exam = planner.get_exam(db, user.id, payload.exam_date_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found")
    mastery = adaptive.topic_mastery_map(db, student.id)
    return planner.generate_plan(
        db,
        user.id,
        student.id,
        exam,
        daily_minutes=payload.daily_minutes,
        subject_id=payload.subject_id,
        mastery=mastery,
    )


@router.get("/plans", response_model=list[PlanSummaryOut])
def list_plans(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PlanSummaryOut]:
    return [_summary(db, plan) for plan in planner.list_plans(db, user.id)]


@router.get("/plans/{plan_id}", response_model=PlanDetailOut)
def get_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanDetailOut:
    return _detail(db, _get_plan(db, user, plan_id))


@router.patch(
    "/plans/{plan_id}/items/{item_id}", response_model=PlanItemOut
)
def update_item(
    plan_id: int,
    item_id: int,
    payload: PlanItemUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanItemOut:
    plan = _get_plan(db, user, plan_id)
    item = db.get(StudyPlanItem, item_id)
    if item is None or item.plan_id != plan.id:
        raise HTTPException(status_code=404, detail="Plan item not found")

    planner.set_item_status(db, item, payload.status)
    titles = _topic_titles(db, [item])

    if payload.status == planner.STATUS_DONE:
        gamification.record_activity(db, user.id)
        gamification.evaluate(db, user.id)

    return _item_out(item, titles)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    plan = _get_plan(db, user, plan_id)
    planner.delete_plan(db, plan)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
