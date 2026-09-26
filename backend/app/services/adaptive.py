from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app import prompts
from app.llm import LLMError, get_llm
from app.models import (
    Chapter,
    Concept,
    Lesson,
    Mastery,
    MasteryEvent,
    Material,
    Question,
    Student,
    StudySession,
    Subject,
    Topic,
)
from app.services.ai_usage import track_ai

ALPHA = 0.35
RETEACH_THRESHOLD = 0.4
ADVANCE_THRESHOLD = 0.8

_FALLBACK = {
    "reteach": "Let's revisit this with a different explanation.",
    "practice": "Let's reinforce this with a few more questions.",
    "advance": "Nice work — let's move on.",
    "complete": "You've mastered this material. Great job!",
}


def update_mastery(
    db: Session,
    student_id: int,
    concept_id: int,
    is_correct: bool,
    difficulty: int,
    *,
    source: str = "quiz",
) -> Mastery:
    """Exponentially-weighted mastery update (see docs/02-data-model.md).

    Every change is also appended to `MasteryEvent`, giving mastery a history.
    """
    record = db.scalar(
        select(Mastery).where(
            Mastery.student_id == student_id, Mastery.concept_id == concept_id
        )
    )
    if record is None:
        record = Mastery(student_id=student_id, concept_id=concept_id, score=0.0)
        db.add(record)
        db.flush()

    previous = record.score
    weight = 0.6 + 0.1 * max(1, min(5, difficulty))
    observed = 1.0 if is_correct else 0.0
    target = weight * observed + (1 - weight) * 0.5
    record.score = max(0.0, min(1.0, (1 - ALPHA) * record.score + ALPHA * target))
    record.attempts += 1
    record.correct += 1 if is_correct else 0

    topic_id = db.scalar(select(Topic.id).where(Topic.concept_id == concept_id))
    db.add(
        MasteryEvent(
            student_id=student_id,
            concept_id=concept_id,
            topic_id=topic_id,
            score=record.score,
            delta=round(record.score - previous, 6),
            is_correct=is_correct,
            source=source,
        )
    )

    db.commit()
    db.refresh(record)
    return record


def topic_mastery(db: Session, student_id: int, topic_id: int) -> float:
    """Assessment mastery for a topic's concept (0.0 if not yet attempted)."""
    topic = db.get(Topic, topic_id)
    if topic is None or topic.concept_id is None:
        return 0.0
    score = db.scalar(
        select(Mastery.score).where(
            Mastery.student_id == student_id,
            Mastery.concept_id == topic.concept_id,
        )
    )
    return round(score or 0.0, 4)


def topic_mastery_map(db: Session, student_id: int) -> dict[int, float]:
    """Topic id -> mastery for every topic owned by the student's materials."""
    rows = db.execute(
        select(Topic.id, Mastery.score)
        .join(Chapter, Chapter.id == Topic.chapter_id)
        .join(Subject, Subject.id == Chapter.subject_id)
        .join(Material, Material.id == Subject.material_id)
        .outerjoin(
            Mastery,
            and_(
                Mastery.concept_id == Topic.concept_id,
                Mastery.student_id == student_id,
            ),
        )
        .where(Material.student_id == student_id)
    ).all()
    return {topic_id: round(score or 0.0, 4) for topic_id, score in rows}


def mastery_history(
    db: Session,
    student_id: int,
    *,
    concept_id: int | None = None,
    topic_id: int | None = None,
    limit: int = 100,
) -> list[MasteryEvent]:
    stmt = select(MasteryEvent).where(MasteryEvent.student_id == student_id)
    if concept_id is not None:
        stmt = stmt.where(MasteryEvent.concept_id == concept_id)
    if topic_id is not None:
        stmt = stmt.where(MasteryEvent.topic_id == topic_id)
    stmt = stmt.order_by(MasteryEvent.created_at.desc(), MasteryEvent.id.desc())
    stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def mastery_map(db: Session, student_id: int, material_id: int) -> dict[int, float]:
    rows = db.execute(
        select(Mastery.concept_id, Mastery.score)
        .join(Concept, Concept.id == Mastery.concept_id)
        .where(Mastery.student_id == student_id, Concept.material_id == material_id)
    ).all()
    return {concept_id: score for concept_id, score in rows}


def next_action(db: Session, session: StudySession) -> dict:
    """Deterministic policy producing the next adaptive step."""
    material = db.get(Material, session.material_id)
    if material is None:
        return {"type": "complete", "message": _FALLBACK["complete"]}

    owner_id = _owner_user_id(db, material)
    concepts = list(
        db.scalars(
            select(Concept)
            .where(Concept.material_id == material.id)
            .order_by(Concept.order_index)
        )
    )
    if not concepts:
        return {"type": "complete", "message": _FALLBACK["complete"]}

    scores = mastery_map(db, session.student_id, material.id)
    by_id = {c.id: c for c in concepts}

    current = by_id.get(session.current_concept_id) if session.current_concept_id else None
    score = scores.get(current.id, 0.0) if current else 0.0

    # Decide whether to stay on the current concept or advance.
    if current is None or score > ADVANCE_THRESHOLD:
        nxt = next(
            (c for c in concepts if scores.get(c.id, 0.0) <= ADVANCE_THRESHOLD),
            None,
        )
        if nxt is None:
            session.status = "completed"
            db.commit()
            return {"type": "complete", "message": _fallback("complete", material)}

        session.current_concept_id = nxt.id
        db.commit()
        lesson = _lesson_for(db, nxt)
        return {
            "type": "advance",
            "message": _message(db, "advance", nxt.title, user_id=owner_id),
            "concept": nxt,
            "lesson": lesson,
        }

    # Stay on current concept: reteach if weak, otherwise practice.
    action = "reteach" if score < RETEACH_THRESHOLD else "practice"
    if action == "reteach":
        lesson = _lesson_for(db, current, simpler=True)
        return {
            "type": "reteach",
            "message": _message(db, "reteach", current.title, user_id=owner_id),
            "concept": current,
            "lesson": lesson,
        }

    lesson = _lesson_for(db, current)
    if lesson is None:
        return {
            "type": "advance",
            "message": _message(db, "advance", current.title, user_id=owner_id),
            "concept": current,
            "lesson": None,
        }
    from app.services.assessment import generate_quiz  # avoid circular import

    questions = generate_quiz(db, lesson)
    return {
        "type": "practice",
        "message": _message(db, "practice", current.title, user_id=owner_id),
        "concept": current,
        "quiz": _quiz_payload(lesson, questions),
    }


def _lesson_for(
    db: Session, concept: Concept, *, simpler: bool = False
) -> Lesson | None:
    from app.services.teaching import generate_lesson  # avoid circular import

    lesson = db.scalar(
        select(Lesson)
        .where(Lesson.concept_id == concept.id, Lesson.simpler.is_(simpler))
        .order_by(Lesson.id.desc())
    )
    if lesson is not None:
        return lesson

    material = db.get(Material, concept.material_id)
    if material is None:
        return None
    try:
        return generate_lesson(db, material, concept, simpler=simpler)
    except (LLMError, ValueError):
        return None


def _quiz_payload(lesson: Lesson, questions: list[Question]) -> dict:
    return {
        "lesson_id": lesson.id,
        "questions": [
            {
                "id": q.id,
                "type": q.type,
                "prompt": q.prompt,
                "options": q.options,
                "difficulty": q.difficulty,
            }
            for q in questions
        ],
    }


def _message(
    db: Session,
    action: str,
    concept_title: str,
    *,
    user_id: int | None = None,
) -> str:
    provider = get_llm()
    try:
        with track_ai(
            db, provider, "adaptive.message", user_id=user_id, commit=True
        ):
            text = provider.complete(
                [
                    {
                        "role": "user",
                        "content": prompts.adaptive.adaptive_user(action, concept_title),
                    }
                ],
                system=prompts.adaptive.ADAPTIVE_SYSTEM,
                max_tokens=60,
                temperature=0.7,
            )
        text = text.strip().strip('"')
        if text:
            return text
    except LLMError:
        pass
    return _FALLBACK[action]


def _fallback(action: str, material: Material) -> str:
    return _FALLBACK[action]


def _owner_user_id(db: Session, material: Material) -> int | None:
    student = db.get(Student, material.student_id) if material.student_id else None
    return student.user_id if student is not None else None
