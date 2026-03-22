"""JWT access and refresh token creation and verification (HS256)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from src.config import jwt_cfg

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def new_access_refresh_jtis() -> tuple[str, str]:
    """Return (access_jti, refresh_jti) for token rotation."""
    return uuid.uuid4().hex, uuid.uuid4().hex


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, jti: str, session_id: str) -> str:
    """Create a short-lived access JWT."""
    now = _now_utc()
    exp = now + timedelta(minutes=jwt_cfg.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": jti,
        "sid": session_id,
        "typ": TOKEN_TYPE_ACCESS,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(
        payload,
        jwt_cfg.jwt_secret,
        algorithm=jwt_cfg.jwt_algorithm,
    )


def create_refresh_token(user_id: int, jti: str, session_id: str) -> str:
    """Create a long-lived refresh JWT."""
    now = _now_utc()
    exp = now + timedelta(days=jwt_cfg.refresh_token_expire_days)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "jti": jti,
        "sid": session_id,
        "typ": TOKEN_TYPE_REFRESH,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(
        payload,
        jwt_cfg.jwt_secret,
        algorithm=jwt_cfg.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Verify signature and expiry; return claims."""
    return jwt.decode(
        token,
        jwt_cfg.jwt_secret,
        algorithms=[jwt_cfg.jwt_algorithm],
    )


def new_token_ids() -> tuple[str, str, str]:
    """Return (session_id, access_jti, refresh_jti)."""
    sid = uuid.uuid4().hex
    return sid, uuid.uuid4().hex, uuid.uuid4().hex
