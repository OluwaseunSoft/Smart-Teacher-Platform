from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ROLE_ADMIN, Material, Student, Topic, User, UserSession
from app.security import ACCESS, TokenError, decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(credentials.credentials, ACCESS)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    session = db.scalar(
        select(UserSession).where(
            UserSession.jti == payload["jti"],
            UserSession.revoked_at.is_(None),
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is no longer valid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive or missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return user


def current_student(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Student:
    """Resolve the authenticated user's Student row, creating it if needed."""
    student = db.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        student = Student(user_id=user.id, name=user.display_name or "Student")
        db.add(student)
        db.commit()
        db.refresh(student)
    return student


def owned_material(db: Session, material_id: int, student: Student) -> Material:
    """Fetch a material only if it belongs to the student (404 otherwise)."""
    material = db.get(Material, material_id)
    if material is None or material.student_id != student.id:
        raise HTTPException(status_code=404, detail="Material not found")
    return material


def owned_topic(db: Session, topic_id: int, student: Student) -> Topic:
    """Fetch a topic only if its material belongs to the student (404 otherwise)."""
    topic = db.get(Topic, topic_id)
    if topic is None or topic.chapter is None or topic.chapter.subject is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    material_id = topic.chapter.subject.material_id
    material = db.get(Material, material_id) if material_id is not None else None
    if material is None or material.student_id != student.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
