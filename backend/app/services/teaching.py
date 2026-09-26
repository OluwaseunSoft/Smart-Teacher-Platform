from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import prompts
from app.llm import get_llm
from app.models import Concept, Lesson, Material, Topic
from app.services.ai_usage import track_ai
from app.services.retrieval import rank_chunks


def generate_lesson(
    db: Session, material: Material, concept: Concept, *, simpler: bool = False
) -> Lesson:
    query = f"{concept.title}. {concept.summary}"
    ranked = rank_chunks(
        db, material.id, query, user_id=_owner_user_id(material)
    )
    excerpts = [chunk.content for chunk, _ in ranked]

    provider = get_llm()
    with track_ai(
        db, provider, "teaching.generate_lesson", user_id=_owner_user_id(material)
    ):
        data = provider.generate_json(
            [
                {
                    "role": "user",
                    "content": prompts.teaching.teaching_user(
                        concept.title, concept.summary, excerpts, simpler=simpler
                    ),
                }
            ],
            system=prompts.teaching.TEACHING_SYSTEM,
            max_tokens=4096,
        )
    if not isinstance(data, dict):
        raise ValueError("Teaching returned an unexpected shape.")

    topic = _topic_for_concept(db, concept.id)
    lesson = Lesson(
        material_id=material.id,
        concept_id=concept.id,
        topic_id=topic.id if topic is not None else None,
        title=str(data.get("title") or concept.title)[:300],
        objectives=[str(o) for o in data.get("objectives", [])][:8],
        content=str(data.get("content_markdown", "")),
        language=_language_for(topic),
        grounding=[{"chunk_id": c.id, "index": c.index} for c, _ in ranked],
        status="ready",
        simpler=simpler,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def _owner_user_id(material: Material) -> int | None:
    student = material.student
    return student.user_id if student is not None else None


def _topic_for_concept(db: Session, concept_id: int) -> Topic | None:
    return db.scalar(
        select(Topic).where(Topic.concept_id == concept_id).order_by(Topic.id)
    )


def _language_for(topic: Topic | None) -> str:
    if topic is None or topic.chapter is None or topic.chapter.subject is None:
        return "en"
    return topic.chapter.subject.language or "en"


def generate_all_lessons(db: Session, material: Material) -> list[Lesson]:
    concepts = list(
        db.scalars(
            select(Concept)
            .where(Concept.material_id == material.id)
            .order_by(Concept.order_index)
        )
    )
    lessons: list[Lesson] = []
    for concept in concepts:
        existing = db.scalar(
            select(Lesson).where(
                Lesson.concept_id == concept.id, Lesson.simpler.is_(False)
            )
        )
        if existing:
            lessons.append(existing)
            continue
        lessons.append(generate_lesson(db, material, concept))
    return lessons


def regenerate_lesson(
    db: Session, lesson: Lesson, *, simpler: bool = False
) -> Lesson:
    concept = db.get(Concept, lesson.concept_id)
    material = db.get(Material, lesson.material_id)
    assert concept is not None and material is not None

    lesson.title = f"{concept.title} (simpler)" if simpler else lesson.title
    lesson.status = "pending"
    db.commit()

    new_lesson = generate_lesson(db, material, concept, simpler=simpler)
    return new_lesson
