from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_material
from app.db import get_db
from app.llm import LLMError
from app.models import Concept, Lesson, StudySession, Student
from app.schemas import (
    ConceptOut,
    LessonOut,
    NextActionOut,
    SessionCreateIn,
    SessionOut,
)
from app.services import adaptive

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _get_session(db: Session, session_id: int, student: Student) -> StudySession:
    session = db.get(StudySession, session_id)
    if session is None or session.student_id != student.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreateIn,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> StudySession:
    material = owned_material(db, payload.material_id, student)
    if material.status != "ready":
        raise HTTPException(
            status_code=400, detail="Material must be processed before studying"
        )

    session = StudySession(student_id=student.id, material_id=material.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> StudySession:
    return _get_session(db, session_id, student)


@router.post("/{session_id}/next", response_model=NextActionOut)
def next_step(
    session_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> NextActionOut:
    session = _get_session(db, session_id, student)

    try:
        action = adaptive.next_action(db, session)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    concept = action.get("concept")
    lesson = action.get("lesson")
    return NextActionOut(
        type=action["type"],
        message=action["message"],
        concept=_to_concept_out(concept) if concept is not None else None,
        lesson=_to_lesson_out(lesson) if lesson is not None else None,
        quiz=action.get("quiz"),
    )


def _to_concept_out(concept: Concept) -> ConceptOut:
    return ConceptOut.model_validate(concept)


def _to_lesson_out(lesson) -> LessonOut:
    return LessonOut.model_validate(lesson)
