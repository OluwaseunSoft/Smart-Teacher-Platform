from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db import get_db
from app.models import AIUsageLog, AuditLog, User, UserSession, utcnow
from app.schemas import (
    AdminUserUpdateIn,
    AIUsageOut,
    AuditLogOut,
    UserOut,
    UserPage,
)
from app.services.audit import record_audit

router = APIRouter(
    prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/users", response_model=UserPage)
def list_users(
    q: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> UserPage:
    statement = select(User)
    count_statement = select(func.count(User.id))
    if q:
        pattern = f"%{q.strip().lower()}%"
        condition = or_(
            func.lower(User.email).like(pattern),
            func.lower(User.display_name).like(pattern),
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = db.scalar(count_statement) or 0
    rows = db.scalars(
        statement.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return UserPage(
        items=[UserOut.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: AdminUserUpdateIn,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.role is not None:
        user.role = payload.role
    if payload.grade is not None:
        user.grade = payload.grade
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.add(user)
    record_audit(
        db,
        actor_user_id=admin.id,
        action="admin.user_updated",
        target_type="user",
        target_id=user.id,
        meta=payload.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")

    user.is_active = False
    for session in db.scalars(
        select(UserSession).where(
            UserSession.user_id == user.id, UserSession.revoked_at.is_(None)
        )
    ):
        session.revoked_at = utcnow()
        db.add(session)
    db.add(user)
    record_audit(
        db,
        actor_user_id=admin.id,
        action="admin.user_deactivated",
        target_type="user",
        target_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reactivate", response_model=UserOut)
def reactivate_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    db.add(user)
    record_audit(
        db,
        actor_user_id=admin.id,
        action="admin.user_reactivated",
        target_type="user",
        target_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/ai-usage", response_model=list[AIUsageOut])
def list_ai_usage(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[AIUsageLog]:
    return list(
        db.scalars(select(AIUsageLog).order_by(AIUsageLog.created_at.desc()).limit(limit))
    )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[AuditLog]:
    return list(
        db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
    )
