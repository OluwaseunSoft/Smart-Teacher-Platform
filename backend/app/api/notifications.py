from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import MarkAllReadOut, NotificationOut, NotificationPage
from app.services import notifications

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=NotificationPage)
def list_notifications(
    generate: bool = Query(default=True),
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationPage:
    if generate:
        notifications.generate_reminders(db, user.id)
    items = notifications.list_notifications(
        db, user.id, unread_only=unread_only, limit=limit
    )
    return NotificationPage(
        items=items, unread=notifications.unread_count(db, user.id)
    )


@router.post("/read-all", response_model=MarkAllReadOut)
def read_all(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MarkAllReadOut:
    return MarkAllReadOut(updated=notifications.mark_all_read(db, user.id))


@router.post("/{notification_id}/read", response_model=NotificationOut)
def read_one(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationOut:
    notification = notifications.get_notification(db, user.id, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notifications.mark_read(db, notification)
