from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_material
from app.db import get_db
from app.models import Material, Student, Subject, Topic
from app.schemas import (
    ChapterOut,
    CurriculumOut,
    GroundingRef,
    LessonSummary,
    SubjectOut,
    TopicDetailOut,
    TopicOut,
)

router = APIRouter(prefix="/api", tags=["curriculum"])


def _subject_out(subject: Subject) -> SubjectOut:
    return SubjectOut(
        id=subject.id,
        material_id=subject.material_id,
        name=subject.name,
        language=subject.language,
        order_index=subject.order_index,
        chapters=[
            ChapterOut(
                id=chapter.id,
                subject_id=chapter.subject_id,
                title=chapter.title,
                order_index=chapter.order_index,
                topics=[TopicOut.model_validate(topic) for topic in chapter.topics],
            )
            for chapter in subject.chapters
        ],
    )


@router.get("/curriculum", response_model=list[CurriculumOut])
def list_curriculum(
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> list[CurriculumOut]:
    material_ids = list(
        db.scalars(select(Material.id).where(Material.student_id == student.id))
    )
    if not material_ids:
        return []

    subjects = list(
        db.scalars(
            select(Subject)
            .where(Subject.material_id.in_(material_ids))
            .order_by(Subject.order_index)
        )
    )
    grouped: dict[int, list[Subject]] = {}
    for subject in subjects:
        grouped.setdefault(subject.material_id, []).append(subject)

    return [
        CurriculumOut(
            material_id=material_id,
            subjects=[_subject_out(s) for s in grouped[material_id]],
        )
        for material_id in material_ids
        if material_id in grouped
    ]


@router.get("/curriculum/materials/{material_id}", response_model=CurriculumOut)
def material_curriculum(
    material_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> CurriculumOut:
    material = owned_material(db, material_id, student)
    subjects = list(
        db.scalars(
            select(Subject)
            .where(Subject.material_id == material.id)
            .order_by(Subject.order_index)
        )
    )
    return CurriculumOut(
        material_id=material.id,
        subjects=[_subject_out(s) for s in subjects],
    )


@router.get("/topics/{topic_id}", response_model=TopicDetailOut)
def get_topic(
    topic_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> TopicDetailOut:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    material = db.get(Material, topic.chapter.subject.material_id)
    if material is None or material.student_id != student.id:
        raise HTTPException(status_code=404, detail="Topic not found")

    return TopicDetailOut(
        id=topic.id,
        chapter_id=topic.chapter_id,
        concept_id=topic.concept_id,
        title=topic.title,
        summary=topic.summary,
        difficulty=topic.difficulty,
        order_index=topic.order_index,
        grounding=[
            GroundingRef(
                chunk_id=link.chunk_id,
                index=link.chunk.index if link.chunk is not None else 0,
                relevance=link.relevance,
            )
            for link in topic.chunk_links
        ],
        lessons=[LessonSummary.model_validate(lesson) for lesson in topic.lessons],
    )
