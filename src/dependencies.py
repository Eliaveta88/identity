"""FastAPI dependencies: JWT bearer auth with Redis blacklist and session checks."""

from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.services.jwt_tokens import TOKEN_TYPE_ACCESS, decode_token
from src.services.redis import is_session_active, is_token_blacklisted

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TokenPayload:
    """Validated access-token claims."""

    user_id: int
    jti: str
    session_id: str


async def get_access_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenPayload:
    """Require ``Authorization: Bearer <access_jwt>`` and validate Redis + session."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        claims = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if claims.get("typ") != TOKEN_TYPE_ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    jti = claims.get("jti")
    sid = claims.get("sid")
    sub = claims.get("sub")
    if not jti or not sid or sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        if await is_token_blacklisted(str(jti)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except HTTPException:
        raise
    except Exception:
        # Redis down: fail closed for protected routes
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    try:
        active = await is_session_active(user_id, str(sid))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )
    if not active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or logged out",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenPayload(user_id=user_id, jti=str(jti), session_id=str(sid))


async def get_current_user_id(payload: TokenPayload = Depends(get_access_token_payload)) -> int:
    """Return authenticated user id from access JWT."""
    return payload.user_id
