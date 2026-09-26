from __future__ import annotations

from sqlalchemy.orm import Session

from app import prompts
from app.llm import get_llm
from app.models import Chapter, Concept, Material, Subject, Topic, TopicChunk
from app.services.ai_usage import track_ai
from app.services.retrieval import rank_chunks


def build_curriculum(db: Session, material: Material) -> list[Concept]:
    """Decompose a material into Subject -> Chapter -> Topic and concepts.

    The explicit hierarchy is persisted for navigation/grounding, while a
    ``Concept`` is created per topic so the adaptive teaching/mastery loop keeps
    working against the same units.
    """
    outline = material.raw_text[:6000]
    provider = get_llm()
    with track_ai(
        db, provider, "structuring", user_id=_owner_user_id(material)
    ):
        data = provider.generate_json(
            [
                {
                    "role": "user",
                    "content": prompts.structuring.structuring_user(
                        material.title, outline
                    ),
                }
            ],
            system=prompts.structuring.STRUCTURING_SYSTEM,
        )
    if not isinstance(data, dict):
        raise ValueError("Structuring returned an unexpected shape.")

    if data.get("title"):
        material.title = str(data["title"])[:300]

    subject = Subject(
        user_id=_owner_user_id(material),
        material_id=material.id,
        name=str(data.get("title") or material.title)[:200],
        language=_language_for(material),
    )
    db.add(subject)
    db.flush()

    concepts: list[Concept] = []
    chapter_order = 0
    topic_order = 0
    for item in data.get("concepts", []):
        if not isinstance(item, dict) or not item.get("title"):
            continue

        chapter = Chapter(
            subject_id=subject.id,
            title=str(item["title"])[:300],
            order_index=chapter_order,
        )
        db.add(chapter)
        db.flush()
        chapter_order += 1

        subconcepts = [
            sub
            for sub in (item.get("subconcepts") or [])
            if isinstance(sub, dict) and sub.get("title")
        ]
        if subconcepts:
            for sub in subconcepts:
                concepts.append(
                    _make_topic(
                        db,
                        material,
                        chapter,
                        title=str(sub["title"])[:300],
                        summary=str(sub.get("summary", "")),
                        difficulty="core",
                        order_index=topic_order,
                    )
                )
                topic_order += 1
        else:
            concepts.append(
                _make_topic(
                    db,
                    material,
                    chapter,
                    title=str(item["title"])[:300],
                    summary=str(item.get("summary", "")),
                    difficulty=_difficulty(item.get("difficulty")),
                    order_index=topic_order,
                )
            )
            topic_order += 1

    db.commit()
    return concepts


def _make_topic(
    db: Session,
    material: Material,
    chapter: Chapter,
    *,
    title: str,
    summary: str,
    difficulty: str,
    order_index: int,
) -> Concept:
    topic = Topic(
        chapter_id=chapter.id,
        title=title,
        summary=summary,
        difficulty=difficulty,
        order_index=order_index,
    )
    db.add(topic)
    db.flush()

    concept = Concept(
        material_id=material.id,
        title=title,
        summary=summary,
        order_index=order_index,
        difficulty=difficulty,
    )
    db.add(concept)
    db.flush()
    topic.concept_id = concept.id

    _ground_topic(db, material, topic)
    return concept


def _ground_topic(db: Session, material: Material, topic: Topic) -> None:
    """Link a topic to its most relevant source chunks (grounding)."""
    query = f"{topic.title}. {topic.summary}"
    for chunk, relevance in rank_chunks(
        db, material.id, query, user_id=_owner_user_id(material)
    ):
        topic.chunk_links.append(
            TopicChunk(chunk_id=chunk.id, relevance=relevance)
        )


def _owner_user_id(material: Material) -> int | None:
    student = material.student
    return student.user_id if student is not None else None


def _language_for(material: Material) -> str:
    student = material.student
    if student is not None and student.user is not None:
        return student.user.language or "en"
    return "en"


def _difficulty(value: object) -> str:
    value = str(value).lower()
    return value if value in {"intro", "core", "advanced"} else "core"
