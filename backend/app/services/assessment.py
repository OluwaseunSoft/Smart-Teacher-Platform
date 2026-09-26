from __future__ import annotations

from contextlib import nullcontext

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import prompts
from app.llm import get_llm
from app.models import Lesson, Material, Question
from app.services.ai_usage import track_ai
from app.services.retrieval import retrieve

VALID_TYPES = {"mcq", "short"}


def generate_quiz(
    db: Session, lesson: Lesson, *, count: int = 4
) -> list[Question]:
    """Generate and persist questions for a lesson (idempotent per lesson)."""
    existing = list(
        db.scalars(select(Question).where(Question.lesson_id == lesson.id))
    )
    if existing:
        return existing

    material = db.get(Material, lesson.material_id)
    excerpts = retrieve(
        db,
        lesson.material_id,
        f"{lesson.title}. {' '.join(lesson.objectives)}",
        user_id=_owner_user_id(material),
    )
    provider = get_llm()
    with track_ai(
        db, provider, "assessment.generate_quiz", user_id=_owner_user_id(material)
    ):
        data = provider.generate_json(
            [
                {
                    "role": "user",
                    "content": prompts.assessment.assessment_user(
                        lesson.title, lesson.objectives, excerpts, count=count
                    ),
                }
            ],
            system=prompts.assessment.ASSESSMENT_SYSTEM,
            max_tokens=4096,
        )

    items = data.get("questions", []) if isinstance(data, dict) else []
    questions: list[Question] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("prompt"):
            continue
        qtype = str(item.get("type", "mcq")).lower()
        if qtype not in VALID_TYPES:
            qtype = "mcq"
        options = item.get("options") if qtype == "mcq" else None
        if qtype == "mcq" and not options:
            qtype = "short"
        questions.append(
            Question(
                lesson_id=lesson.id,
                concept_id=lesson.concept_id,
                type=qtype,
                prompt=str(item["prompt"]),
                options=[str(o) for o in options] if options else None,
                answer=str(item.get("answer", "")),
                explanation=str(item.get("explanation", "")),
                difficulty=_difficulty(item.get("difficulty")),
            )
        )
        db.add(questions[-1])

    db.commit()
    for q in questions:
        db.refresh(q)
    return questions


def grade_answer(
    question: Question,
    response: str,
    *,
    db: Session | None = None,
    user_id: int | None = None,
) -> tuple[bool, str]:
    """Return (is_correct, explanation).

    ``db``/``user_id`` are optional so short-answer grading can be recorded in the
    AI-usage log; callers that omit them still grade without logging.
    """
    response = (response or "").strip()
    if not response:
        return False, question.explanation

    if question.type == "mcq":
        correct = _normalize(response) == _normalize(question.answer)
        if not correct and question.options:
            # allow answering by option letter, e.g. "B" or "b)"
            for i, option in enumerate(question.options):
                letter = chr(ord("A") + i)
                if _normalize(response) in {letter.lower(), f"{letter.lower()})"}:
                    if _normalize(option) == _normalize(question.answer):
                        correct = True
                        break
        return correct, question.explanation

    provider = get_llm()
    tracker = (
        track_ai(db, provider, "assessment.grade", user_id=user_id)
        if db is not None
        else nullcontext()
    )
    with tracker:
        data = provider.generate_json(
            [
                {
                    "role": "user",
                    "content": prompts.assessment.grading_user(
                        question.prompt, question.answer, response
                    ),
                }
            ],
            system=prompts.assessment.GRADING_SYSTEM,
            max_tokens=512,
        )
    if isinstance(data, dict):
        return bool(data.get("correct")), str(
            data.get("explanation") or question.explanation
        )
    return False, question.explanation


def _owner_user_id(material: Material | None) -> int | None:
    if material is None:
        return None
    student = material.student
    return student.user_id if student is not None else None


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().split()).rstrip(".")


def _difficulty(value: object) -> int:
    try:
        return max(1, min(5, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 2
