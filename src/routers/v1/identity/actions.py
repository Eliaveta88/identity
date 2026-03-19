"""Business logic actions for identity endpoints."""

from fastapi import HTTPException, status

from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.schemas import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)


async def _login(
    credentials: LoginRequest,
    dal: UserDAL,
) -> LoginResponse:
    """Authenticate user and return tokens."""
    user = await dal.get_by_username(credentials.username)
    if not user or not dal.verify_password(credentials.password, user.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    
    # TODO: Generate JWT tokens
    return LoginResponse(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        token_type="bearer",
        user=UserResponse(**user),
    )


async def _get_current_user(
    user_id: int,
    dal: UserDAL,
) -> UserResponse:
    """Get current authenticated user."""
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
) -> dict:
    """Logout user (revoke token)."""
    # TODO: Implement token revocation logic
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
