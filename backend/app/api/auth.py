from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.db import get_db
from app.models import ROLE_STUDENT, StudentProfile, User, UserSession, utcnow
from app.schemas import (
    LoginIn,
    PasswordResetConfirmIn,
    PasswordResetRequestIn,
    PasswordResetRequestOut,
    ProfileUpdateIn,
    RefreshIn,
    SignupIn,
    TokenOut,
    UserOut,
)
from app.security import (
    ACCESS,
    REFRESH,
    RESET,
    TokenError,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.audit import record_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


def _issue_tokens(db: Session, user: User, user_agent: str | None) -> TokenOut:
    access_token, access_jti, access_exp = create_access_token(user.id)
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(user.id)
    db.add_all(
        [
            UserSession(
                user_id=user.id,
                jti=access_jti,
                token_type=ACCESS,
                expires_at=access_exp,
                user_agent=user_agent,
            ),
            UserSession(
                user_id=user.id,
                jti=refresh_jti,
                token_type=REFRESH,
                expires_at=refresh_exp,
                user_agent=user_agent,
            ),
        ]
    )
    db.commit()
    return TokenOut(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(
    payload: SignupIn, request: Request, db: Session = Depends(get_db)
) -> TokenOut:
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="Email is already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=ROLE_STUDENT,
        display_name=payload.display_name,
        grade=payload.grade,
        language=payload.language,
        timezone=payload.timezone,
    )
    db.add(user)
    db.flush()
    db.add(StudentProfile(user_id=user.id))
    record_audit(db, actor_user_id=user.id, action="auth.signup", target_type="user", target_id=user.id)
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user, request.headers.get("user-agent"))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)) -> TokenOut:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    record_audit(db, actor_user_id=user.id, action="auth.login", target_type="user", target_id=user.id)
    db.commit()
    return _issue_tokens(db, user, request.headers.get("user-agent"))


@router.post("/refresh", response_model=TokenOut)
def refresh(
    payload: RefreshIn, request: Request, db: Session = Depends(get_db)
) -> TokenOut:
    try:
        claims = decode_token(payload.refresh_token, REFRESH)
    except TokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc

    session = db.scalar(
        select(UserSession).where(
            UserSession.jti == claims["jti"], UserSession.revoked_at.is_(None)
        )
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Refresh token is no longer valid")

    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive or missing")

    session.revoked_at = session.expires_at
    db.add(session)
    db.commit()
    return _issue_tokens(db, user, request.headers.get("user-agent"))


@router.post("/logout", status_code=204)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> None:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        claims = decode_token(credentials.credentials, ACCESS)
    except TokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    session = db.scalar(
        select(UserSession).where(UserSession.jti == claims["jti"])
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = utcnow()
        db.add(session)
        record_audit(
            db,
            actor_user_id=session.user_id,
            action="auth.logout",
            target_type="user",
            target_id=session.user_id,
        )
        db.commit()


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    payload: ProfileUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    if payload.display_name is not None:
        user.display_name = payload.display_name
    if payload.grade is not None:
        user.grade = payload.grade
    if payload.language is not None:
        user.language = payload.language
    if payload.timezone is not None:
        user.timezone = payload.timezone
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/password-reset/request", response_model=PasswordResetRequestOut)
def request_password_reset(
    payload: PasswordResetRequestIn, db: Session = Depends(get_db)
) -> PasswordResetRequestOut:
    detail = "If that email is registered, a reset link has been sent."
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None:
        return PasswordResetRequestOut(detail=detail)

    token, jti, expires = create_reset_token(user.id)
    db.add(
        UserSession(
            user_id=user.id,
            jti=jti,
            token_type=RESET,
            expires_at=expires,
        )
    )
    record_audit(
        db,
        actor_user_id=user.id,
        action="auth.password_reset_requested",
        target_type="user",
        target_id=user.id,
    )
    db.commit()
    exposed = token if settings.AUTH_EXPOSE_RESET_TOKEN else None
    return PasswordResetRequestOut(detail=detail, reset_token=exposed)


@router.post("/password-reset/confirm")
def confirm_password_reset(
    payload: PasswordResetConfirmIn, db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        claims = decode_token(payload.token, RESET)
    except TokenError as exc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token") from exc

    session = db.scalar(
        select(UserSession).where(
            UserSession.jti == claims["jti"], UserSession.revoked_at.is_(None)
        )
    )
    if session is None:
        raise HTTPException(status_code=400, detail="Reset token is no longer valid")

    user = db.get(User, int(claims["sub"]))
    if user is None:
        raise HTTPException(status_code=400, detail="Account not found")

    user.password_hash = hash_password(payload.new_password)
    session.revoked_at = utcnow()
    for active in db.scalars(
        select(UserSession).where(
            UserSession.user_id == user.id, UserSession.revoked_at.is_(None)
        )
    ):
        active.revoked_at = utcnow()
        db.add(active)
    db.add(user)
    record_audit(
        db,
        actor_user_id=user.id,
        action="auth.password_reset_completed",
        target_type="user",
        target_id=user.id,
    )
    db.commit()
    return {"detail": "Password has been reset."}
