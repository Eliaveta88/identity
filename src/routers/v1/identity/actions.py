"""Business logic actions for identity endpoints."""

from __future__ import annotations

import logging
import time

import jwt as pyjwt

from fastapi import HTTPException, status

from src.config import jwt_cfg
from src.dependencies import TokenPayload
from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    UserCreate,
    UserResponse,
)
from src.services.jwt_tokens import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    new_access_refresh_jtis,
    new_token_ids,
)
from src.services.redis import (
    blacklist_token,
    check_rate_limit,
    is_session_active,
    is_token_blacklisted,
    register_session,
    reset_rate_limit,
    revoke_all_sessions,
    revoke_session,
)


logger = logging.getLogger(__name__)


def _access_blacklist_ttl_seconds() -> int:
    return max(jwt_cfg.access_token_expire_minutes * 60, 60)


async def _login(
    credentials: LoginRequest,
    dal: UserDAL,
) -> LoginResponse:
    """Authenticate user and return JWT access + refresh tokens."""
    rate_key = f"login:{credentials.username.lower()}"
    try:
        allowed, _ = await check_rate_limit(
            key=rate_key,
            max_attempts=5,
            window_seconds=300,
        )
    except Exception:
        logger.exception("Rate limit check failed for username '%s'", credentials.username)
        allowed = True

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = await dal.get_by_username(credentials.username)
    if not user or not dal.verify_password(credentials.password, user.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    user_id = int(user["id"])
    session_id, access_jti, refresh_jti = new_token_ids()
    refresh_ttl = jwt_cfg.refresh_token_expire_days * 86400

    access_token = create_access_token(user_id, access_jti, session_id)
    refresh_token = create_refresh_token(user_id, refresh_jti, session_id)

    try:
        await reset_rate_limit(rate_key)
    except Exception:
        logger.exception("Failed to reset rate limit for username '%s'", credentials.username)

    try:
        await register_session(user_id, session_id, ttl_seconds=refresh_ttl)
    except Exception:
        logger.exception("Failed to register session for user_id '%s'", user_id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(**user),
    )


async def _refresh_tokens(
    body: RefreshTokenRequest,
    dal: UserDAL,
) -> LoginResponse:
    """Issue new access + refresh JWTs; blacklist the used refresh token."""
    try:
        claims = decode_token(body.refresh_token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if claims.get("typ") != TOKEN_TYPE_REFRESH:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    old_jti = claims.get("jti")
    sid = claims.get("sid")
    sub = claims.get("sub")
    if not old_jti or not sid or sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token claims",
        )

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject",
        )

    try:
        if await is_token_blacklisted(str(old_jti)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Redis blacklist check failed during refresh")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    try:
        if not await is_session_active(user_id, str(sid)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired or logged out",
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Redis session check failed during refresh")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    exp = claims.get("exp")
    if isinstance(exp, (int, float)):
        remaining = max(int(exp) - int(time.time()), 1)
    else:
        remaining = jwt_cfg.refresh_token_expire_days * 86400

    try:
        await blacklist_token(str(old_jti), ttl_seconds=remaining)
    except Exception:
        logger.exception("Failed to blacklist old refresh token")

    access_jti, refresh_jti = new_access_refresh_jtis()
    access_token = create_access_token(user_id, access_jti, str(sid))
    refresh_token = create_refresh_token(user_id, refresh_jti, str(sid))

    user = await dal.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=UserResponse(**user),
    )


async def _get_current_user(
    user_id: int,
    dal: UserDAL,
) -> UserResponse:
    """Get current authenticated user (JWT already validated by dependency)."""
    user = await dal.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(**user)


async def _logout(
    payload: TokenPayload,
    dal: UserDAL,
) -> dict:
    """Logout: blacklist access token jti and drop session from Redis."""
    try:
        await blacklist_token(payload.jti, ttl_seconds=_access_blacklist_ttl_seconds())
    except Exception:
        logger.exception("Failed to blacklist token for user_id '%s'", payload.user_id)

    try:
        await revoke_session(payload.user_id, payload.session_id)
    except Exception:
        logger.exception("Failed to revoke session for user_id '%s'", payload.user_id)

    return {"status": "ok"}


async def _logout_all(
    user_id: int,
    dal: UserDAL,
) -> dict:
    """Logout user from all active sessions."""
    try:
        await revoke_all_sessions(user_id)
    except Exception:
        logger.exception("Failed to revoke all sessions for user_id '%s'", user_id)

    return {"status": "ok"}


async def _create_user(
    user_in: UserCreate,
    dal: UserDAL,
) -> UserResponse:
    """Create new user."""
    existing = await dal.get_by_username(user_in.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    existing_email = await dal.get_by_email(user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user = await dal.create(user_in)
    return UserResponse(**user)
