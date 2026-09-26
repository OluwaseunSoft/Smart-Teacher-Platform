from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import prompts
from app.llm import get_llm
from app.models import (
    Material,
    Topic,
    TutorConversation,
    TutorMessage,
    User,
    utcnow,
)
from app.services.ai_usage import track_ai
from app.services.retrieval import rank_chunks

MAX_HISTORY = 20
_FALLBACK_REPLY = "Let's think it through together — what do you already know about this?"


def create_conversation(
    db: Session,
    user: User,
    topic: Topic | None = None,
    *,
    title: str | None = None,
    language: str | None = None,
) -> TutorConversation:
    default_title = topic.title if topic is not None else "New conversation"
    conversation = TutorConversation(
        user_id=user.id,
        topic_id=topic.id if topic is not None else None,
        title=(title or default_title)[:200],
        language=language or user.language or "en",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def list_conversations(
    db: Session, user_id: int, *, limit: int = 50
) -> list[TutorConversation]:
    return list(
        db.scalars(
            select(TutorConversation)
            .where(TutorConversation.user_id == user_id)
            .order_by(
                TutorConversation.updated_at.desc(), TutorConversation.id.desc()
            )
            .limit(limit)
        )
    )


def get_conversation(
    db: Session, user_id: int, conversation_id: int
) -> TutorConversation | None:
    conversation = db.get(TutorConversation, conversation_id)
    if conversation is None or conversation.user_id != user_id:
        return None
    return conversation


def messages(
    db: Session, conversation_id: int, *, limit: int | None = None
) -> list[TutorMessage]:
    stmt = (
        select(TutorMessage)
        .where(TutorMessage.conversation_id == conversation_id)
        .order_by(TutorMessage.id)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt))


def message_count(db: Session, conversation_id: int) -> int:
    return len(messages(db, conversation_id))


def topic_context(
    db: Session, topic: Topic | None, *, user_id: int | None = None
) -> tuple[str, str, list[str], list[dict]]:
    """Return (title, summary, excerpts, grounding refs) for a topic's material."""
    if topic is None:
        return "", "", [], []

    material = _material_for_topic(db, topic)
    if material is None:
        return topic.title, topic.summary, [], []

    query = f"{topic.title}. {topic.summary}".strip()
    ranked = rank_chunks(db, material.id, query, user_id=user_id)
    excerpts = [chunk.content for chunk, _ in ranked]
    grounding = [
        {"chunk_id": chunk.id, "index": chunk.index, "relevance": round(score, 4)}
        for chunk, score in ranked
    ]
    return topic.title, topic.summary, excerpts, grounding


def ask(
    db: Session,
    conversation: TutorConversation,
    content: str,
    *,
    topic: Topic | None = None,
    mastery: float | None = None,
) -> tuple[TutorMessage, TutorMessage]:
    """Persist the student's message and return (student_message, tutor_reply).

    The student's message is committed before the provider call so the
    conversation survives an LLM failure.
    """
    student_message = TutorMessage(
        conversation_id=conversation.id, role="user", content=content
    )
    db.add(student_message)
    db.commit()
    db.refresh(student_message)

    title, summary, excerpts, grounding = topic_context(
        db, topic, user_id=conversation.user_id
    )
    system = prompts.tutor.tutor_system(
        title, summary, excerpts, mastery=mastery
    )
    chat = [
        {"role": message.role, "content": message.content}
        for message in _recent_messages(db, conversation.id)
    ]

    provider = get_llm()
    with track_ai(
        db, provider, "tutor.reply", user_id=conversation.user_id
    ):
        raw = provider.complete(
            chat, system=system, temperature=0.5, max_tokens=400
        )
    reply_text = (raw or "").strip() or _FALLBACK_REPLY

    reply = TutorMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        grounding=grounding,
    )
    db.add(reply)
    conversation.updated_at = utcnow()
    db.commit()
    db.refresh(reply)
    return student_message, reply


def delete_conversation(db: Session, conversation: TutorConversation) -> None:
    db.delete(conversation)
    db.commit()


def _recent_messages(db: Session, conversation_id: int) -> list[TutorMessage]:
    rows = list(
        db.scalars(
            select(TutorMessage)
            .where(TutorMessage.conversation_id == conversation_id)
            .order_by(TutorMessage.id.desc())
            .limit(MAX_HISTORY)
        )
    )
    return list(reversed(rows))


def _material_for_topic(db: Session, topic: Topic) -> Material | None:
    if topic.chapter is None or topic.chapter.subject is None:
        return None
    material_id = topic.chapter.subject.material_id
    return db.get(Material, material_id) if material_id is not None else None
