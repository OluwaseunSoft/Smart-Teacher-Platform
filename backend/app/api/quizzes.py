from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_student, owned_material
from app.db import get_db
from app.llm import LLMError
from app.models import Attempt, Lesson, Question, Student
from app.schemas import (
    ConceptMasteryOut,
    QuestionResult,
    QuizResultOut,
    QuizSubmitIn,
)
from app.services import adaptive, assessment, gamification, notifications, repetition

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


@router.post("/{lesson_id}/submit", response_model=QuizResultOut)
def submit_quiz(
    lesson_id: int,
    payload: QuizSubmitIn,
    student: Student = Depends(current_student),
    db: Session = Depends(get_db),
) -> QuizResultOut:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    owned_material(db, lesson.material_id, student)

    questions = {
        q.id: q
        for q in db.scalars(select(Question).where(Question.lesson_id == lesson_id))
    }
    if not questions:
        raise HTTPException(status_code=404, detail="No quiz for this lesson")

    results: list[QuestionResult] = []
    touched_concepts: set[int] = set()
    correct_count = 0

    for answer in payload.answers:
        question = questions.get(answer.question_id)
        if question is None:
            continue
        try:
            is_correct, explanation = assessment.grade_answer(
                question, answer.response, db=db, user_id=student.user_id
            )
        except LLMError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        db.add(
            Attempt(
                student_id=student.id,
                question_id=question.id,
                response=answer.response,
                is_correct=is_correct,
            )
        )
        adaptive.update_mastery(
            db, student.id, question.concept_id, is_correct, question.difficulty
        )
        touched_concepts.add(question.concept_id)
        correct_count += 1 if is_correct else 0

        results.append(
            QuestionResult(
                question_id=question.id,
                correct=is_correct,
                correct_answer=question.answer,
                explanation=explanation,
            )
        )

    db.commit()

    score = correct_count / len(results) if results else 0.0

    # Feed the topic's spaced-repetition schedule from the quiz outcome.
    if results and lesson.topic_id is not None and student.user_id is not None:
        repetition.record_review(
            db,
            student.user_id,
            lesson.topic_id,
            repetition.quality_from_score(score),
        )

    if student.user_id is not None:
        unlocked = gamification.record_and_evaluate(
            db, student.user_id, context={"quiz_score": score}
        )
        notifications.notify_unlocked(db, student.user_id, unlocked)

    scores = adaptive.mastery_map(db, student.id, lesson.material_id)
    return QuizResultOut(
        lesson_id=lesson_id,
        score=score,
        results=results,
        concept_mastery=[
            ConceptMasteryOut(concept_id=cid, score=scores.get(cid, 0.0))
            for cid in sorted(touched_concepts)
        ],
    )
