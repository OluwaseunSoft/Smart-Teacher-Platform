from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_material
from app.db import get_db
from app.llm import LLMError
from app.models import Concept, Lesson, Question, Student
from app.schemas import (
    LessonOut,
    QuestionPublic,
    QuizOut,
    RegenerateLessonIn,
)
from app.services import assessment, teaching

router = APIRouter(prefix="/api", tags=["lessons"])


def _get_lesson(db: Session, lesson_id: int, student: Student) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    owned_material(db, lesson.material_id, student)
    return lesson


@router.get("/lessons/{lesson_id}", response_model=LessonOut)
def get_lesson(
    lesson_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Lesson:
    return _get_lesson(db, lesson_id, student)


@router.post("/lessons/{lesson_id}/regenerate", response_model=LessonOut)
def regenerate(
    lesson_id: int,
    payload: RegenerateLessonIn,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> Lesson:
    lesson = _get_lesson(db, lesson_id, student)
    try:
        return teaching.regenerate_lesson(db, lesson, simpler=payload.simpler)
    except (LLMError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/lessons/{lesson_id}/quiz", response_model=QuizOut)
def get_quiz(
    lesson_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> QuizOut:
    lesson = _get_lesson(db, lesson_id, student)
    questions = list(
        db.scalars(select(Question).where(Question.lesson_id == lesson.id))
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz generated yet")
    return _quiz_out(lesson, questions)


@router.post("/lessons/{lesson_id}/quiz", response_model=QuizOut)
def create_quiz(
    lesson_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> QuizOut:
    lesson = _get_lesson(db, lesson_id, student)
    try:
        questions = assessment.generate_quiz(db, lesson)
    except (LLMError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _quiz_out(lesson, questions)


@router.get("/concepts/{concept_id}")
def get_concept(
    concept_id: int,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> dict:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    owned_material(db, concept.material_id, student)
    return {
        "id": concept.id,
        "material_id": concept.material_id,
        "parent_id": concept.parent_id,
        "title": concept.title,
        "summary": concept.summary,
        "order_index": concept.order_index,
        "difficulty": concept.difficulty,
    }


def _quiz_out(lesson: Lesson, questions: list[Question]) -> QuizOut:
    return QuizOut(
        lesson_id=lesson.id,
        questions=[
            QuestionPublic(
                id=q.id,
                type=q.type,
                prompt=q.prompt,
                options=q.options,
                difficulty=q.difficulty,
            )
            for q in questions
        ],
    )
