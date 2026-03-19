"""Business logic actions for identity endpoints."""

import logging

from fastapi import HTTPException, status

from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.schemas import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from src.services.redis import (
    blacklist_token,
    check_rate_limit,
    is_token_blacklisted,
    register_session,
    reset_rate_limit,
    revoke_all_sessions,
    revoke_session,
)


logger = logging.getLogger(__name__)


async def _login(
    credentials: LoginRequest,
    dal: UserDAL,
) -> LoginResponse:
    """Authenticate user and return tokens."""
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
    session_id = f"session-{user_id}"

    try:
        await reset_rate_limit(rate_key)
    except Exception:
        logger.exception("Failed to reset rate limit for username '%s'", credentials.username)

    try:
        await register_session(user_id, session_id, ttl_seconds=1800)
    except Exception:
        logger.exception("Failed to register session for user_id '%s'", user_id)

    # TODO: Replace mock tokens with real JWT generation.
    return LoginResponse(
        access_token=f"mock_access_token_{user_id}",
        refresh_token=f"mock_refresh_token_{user_id}",
        token_type="bearer",
        user=UserResponse(**user),
    )


async def _get_current_user(
    user_id: int,
    dal: UserDAL,
    token_jti: str | None = None,
) -> UserResponse:
    """Get current authenticated user."""
    if token_jti:
        try:
            if await is_token_blacklisted(token_jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                )
        except HTTPException:
            raise
        except Exception:
            logger.exception("Failed to check token blacklist for jti '%s'", token_jti)

    user = await dal.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse(**user)


async def _logout(
    user_id: int,
    dal: UserDAL,
    token_jti: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Logout user (revoke token)."""
    if token_jti:
        try:
            await blacklist_token(token_jti, ttl_seconds=1800)
        except Exception:
            logger.exception("Failed to blacklist token for user_id '%s'", user_id)

    try:
        if session_id:
            await revoke_session(user_id, session_id)
        else:
            await revoke_all_sessions(user_id)
    except Exception:
        logger.exception("Failed to revoke session(s) for user_id '%s'", user_id)

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
    # Check if user already exists
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
