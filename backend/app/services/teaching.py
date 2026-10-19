from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import prompts
from app.llm import get_llm
from app.llm.base import LLMOutputTruncated
from app.models import Concept, Lesson, Material, Topic
from app.services.ai_usage import track_ai
from app.services.retrieval import rank_chunks


class _LessonResponse(BaseModel):
    title: str = Field(min_length=1)
    objectives: list[str]
    content_markdown: str = Field(min_length=1)


def generate_lesson(
    db: Session, material: Material, concept: Concept, *, simpler: bool = False
) -> Lesson:
    query = f"{concept.title}. {concept.summary}"
    ranked = rank_chunks(
        db, material.id, query, user_id=_owner_user_id(material)
    )
    excerpts = [chunk.content for chunk, _ in ranked]

    provider = get_llm()
    messages = [{
        "role": "user",
        "content": prompts.teaching.teaching_user(
            concept.title, concept.summary, excerpts, simpler=simpler
        ),
    }]
    for attempt in range(2):
        data = None
        try:
            with track_ai(
                db, provider, "teaching.generate_lesson", user_id=_owner_user_id(material)
            ):
                data = provider.generate_json(
                    messages,
                    system=prompts.teaching.TEACHING_SYSTEM,
                    max_tokens=4096 if attempt == 0 else 8192,
                )
                response = _LessonResponse.model_validate(data)
                if not response.title.strip() or not response.content_markdown.strip():
                    raise ValueError("Lesson title and content must not be blank.")
            break
        except (ValidationError, ValueError, LLMOutputTruncated) as exc:
            if attempt:
                raise ValueError(
                    "The AI could not produce a valid lesson after two attempts. "
                    "Please retry processing the material."
                ) from exc
            messages = messages + [
                {"role": "assistant", "content": json.dumps(data, ensure_ascii=False)},
                {"role": "user", "content": (
                    "Return one JSON object, not an array or string. It must have "
                    "a non-empty string title, an objectives array of strings, and "
                    "a non-empty content_markdown string containing the lesson. "
                    "Use the original concept and source excerpts."
                    " Keep the lesson concise (about 400-600 words) so the JSON "
                    "can finish within the output limit."
                )},
            ]

    topic = _topic_for_concept(db, concept.id)
    lesson = Lesson(
        material_id=material.id,
        concept_id=concept.id,
        topic_id=topic.id if topic is not None else None,
        title=response.title[:300],
        objectives=response.objectives[:8],
        content=response.content_markdown,
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
