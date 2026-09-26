from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt

from app.config import settings

ACCESS = "access"
REFRESH = "refresh"
RESET = "reset"


class TokenError(Exception):
    """Raised when a token is missing, malformed, expired, or of the wrong type."""


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _encode(payload: dict) -> str:
    return jwt.encode(payload, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM)


def _issue(subject: int, token_type: str, expires_delta: timedelta) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + expires_delta
    jti = uuid4().hex
    payload = {
        "sub": str(subject),
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": expires,
    }
    return _encode(payload), jti, expires


def create_access_token(user_id: int) -> tuple[str, str, datetime]:
    return _issue(user_id, ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    return _issue(user_id, REFRESH, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def create_reset_token(user_id: int) -> tuple[str, str, datetime]:
    return _issue(user_id, RESET, timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES))


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.AUTH_SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM]
        )
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected {expected_type} token")
    if not payload.get("jti") or not payload.get("sub"):
        raise TokenError("Malformed token")
    return payload
