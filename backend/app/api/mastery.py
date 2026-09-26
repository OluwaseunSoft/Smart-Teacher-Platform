from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_topic
from app.db import get_db
from app.models import Chapter, Material, Student, Subject, Topic
from app.schemas import MasteryEventOut, TopicMasteryOut
from app.services import adaptive

router = APIRouter(prefix="/api/mastery", tags=["mastery"])


@router.get("", response_model=list[TopicMasteryOut])
def list_mastery(
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[TopicMasteryOut]:
    rows = db.execute(
        select(Topic.id, Topic.title, Topic.concept_id)
        .join(Chapter, Chapter.id == Topic.chapter_id)
        .join(Subject, Subject.id == Chapter.subject_id)
        .join(Material, Material.id == Subject.material_id)
        .where(Material.student_id == student.id)
        .order_by(Subject.order_index, Chapter.order_index, Topic.order_index)
    ).all()

    scores = adaptive.topic_mastery_map(db, student.id)
    return [
        TopicMasteryOut(
            topic_id=topic_id,
            title=title,
            concept_id=concept_id,
            mastery=scores.get(topic_id, 0.0),
        )
        for topic_id, title, concept_id in rows
    ]


@router.get("/topics/{topic_id}/history", response_model=list[MasteryEventOut])
def topic_history(
    topic_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[MasteryEventOut]:
    owned_topic(db, topic_id, student)
    events = adaptive.mastery_history(db, student.id, topic_id=topic_id, limit=limit)
    return [MasteryEventOut.model_validate(event) for event in events]
