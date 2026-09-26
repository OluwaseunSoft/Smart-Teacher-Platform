from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import current_student, get_current_user, owned_topic
from app.db import get_db
from app.llm import LLMError
from app.models import Student, Topic, TutorConversation, User
from app.schemas import (
    TutorAskIn,
    TutorConversationCreateIn,
    TutorConversationDetailOut,
    TutorConversationOut,
    TutorConversationSummaryOut,
    TutorReplyOut,
)
from app.services import adaptive, gamification, notifications, tutor

router = APIRouter(prefix="/api/tutor", tags=["tutor"])


def _topic_title(db: Session, conversation: TutorConversation) -> str:
    if conversation.topic_id is None:
        return ""
    topic = db.get(Topic, conversation.topic_id)
    return topic.title if topic is not None else ""


def _summary(
    db: Session, conversation: TutorConversation
) -> TutorConversationSummaryOut:
    return TutorConversationSummaryOut(
        id=conversation.id,
        topic_id=conversation.topic_id,
        title=conversation.title,
        language=conversation.language,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        topic_title=_topic_title(db, conversation),
        message_count=tutor.message_count(db, conversation.id),
    )


def _detail(
    db: Session, conversation: TutorConversation
) -> TutorConversationDetailOut:
    return TutorConversationDetailOut(
        id=conversation.id,
        topic_id=conversation.topic_id,
        title=conversation.title,
        language=conversation.language,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        topic_title=_topic_title(db, conversation),
        messages=tutor.messages(db, conversation.id),
    )


def _get_owned(
    db: Session, user: User, conversation_id: int
) -> TutorConversation:
    conversation = tutor.get_conversation(db, user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/conversations", response_model=list[TutorConversationSummaryOut])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TutorConversationSummaryOut]:
    return [_summary(db, c) for c in tutor.list_conversations(db, user.id)]


@router.post(
    "/conversations",
    response_model=TutorConversationOut,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: TutorConversationCreateIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TutorConversation:
    topic = (
        owned_topic(db, payload.topic_id, student)
        if payload.topic_id is not None
        else None
    )
    conversation = tutor.create_conversation(
        db, user, topic, title=payload.title, language=payload.language
    )
    unlocked = gamification.record_and_evaluate(db, user.id)
    notifications.notify_unlocked(db, user.id, unlocked)
    return conversation


@router.get(
    "/conversations/{conversation_id}",
    response_model=TutorConversationDetailOut,
)
def get_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TutorConversationDetailOut:
    return _detail(db, _get_owned(db, user, conversation_id))


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=TutorReplyOut,
)
def send_message(
    conversation_id: int,
    payload: TutorAskIn,
    student: Student = Depends(current_student),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TutorReplyOut:
    conversation = _get_owned(db, user, conversation_id)
    topic = (
        db.get(Topic, conversation.topic_id)
        if conversation.topic_id is not None
        else None
    )
    mastery = (
        adaptive.topic_mastery(db, student.id, topic.id)
        if topic is not None
        else None
    )
    try:
        student_message, reply = tutor.ask(
            db, conversation, payload.content, topic=topic, mastery=mastery
        )
    except (LLMError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    unlocked = gamification.record_and_evaluate(db, user.id)
    notifications.notify_unlocked(db, user.id, unlocked)
    return TutorReplyOut(user_message=student_message, reply=reply)


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    conversation = _get_owned(db, user, conversation_id)
    tutor.delete_conversation(db, conversation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
