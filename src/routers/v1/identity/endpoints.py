"""Identity v1 endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.core import get_async_session
from src.routers.v1.identity.actions import (
    _create_user,
    _get_current_user,
    _login,
    _logout,
    _logout_all,
)
from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.description import (
    CREATE_USER_DESC,
    GET_CURRENT_USER_DESC,
    LOGIN_DESC,
    LOGOUT_DESC,
    LOGOUT_ALL_DESC,
)
from src.routers.v1.identity.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    UserCreate,
    UserResponse,
)
from src.routers.v1.identity.summary import (
    CREATE_USER_SUMMARY,
    GET_CURRENT_USER_SUMMARY,
    LOGIN_SUMMARY,
    LOGOUT_SUMMARY,
    LOGOUT_ALL_SUMMARY,
)

identity_router = APIRouter(prefix="/identity", tags=["identity"])


async def get_dal(
    session: AsyncSession = Depends(get_async_session),
) -> UserDAL:
    """Dependency: get UserDAL instance."""
    return UserDAL(session=session)


@identity_router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary=LOGIN_SUMMARY,
    description=LOGIN_DESC,
)
async def login(
    credentials: LoginRequest,
    dal: UserDAL = Depends(get_dal),
) -> LoginResponse:
    """Authenticate user."""
    return await _login(credentials, dal)


@identity_router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary=LOGOUT_SUMMARY,
    description=LOGOUT_DESC,
)
async def logout(
    user_id: Annotated[int, Depends(lambda: 1)],  # TODO: Extract from JWT
    token_jti: Annotated[str | None, Header(alias="X-Token-JTI")] = None,
    session_id: Annotated[str | None, Header(alias="X-Session-ID")] = None,
    dal: UserDAL = Depends(get_dal),
) -> LogoutResponse:
    """Logout user."""
    result = await _logout(user_id, dal, token_jti=token_jti, session_id=session_id)
    return LogoutResponse(**result)


@identity_router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary=GET_CURRENT_USER_SUMMARY,
    description=GET_CURRENT_USER_DESC,
)
async def get_current_user(
    user_id: Annotated[int, Depends(lambda: 1)],  # TODO: Extract from JWT
    token_jti: Annotated[str | None, Header(alias="X-Token-JTI")] = None,
    dal: UserDAL = Depends(get_dal),
) -> UserResponse:
    """Get current user."""
    return await _get_current_user(user_id, dal, token_jti=token_jti)


@identity_router.post(
    "/logout-all",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary=LOGOUT_ALL_SUMMARY,
    description=LOGOUT_ALL_DESC,
)
async def logout_all(
    user_id: Annotated[int, Depends(lambda: 1)],  # TODO: Extract from JWT
    dal: UserDAL = Depends(get_dal),
) -> LogoutResponse:
    """Logout user from all sessions."""
    result = await _logout_all(user_id, dal)
    return LogoutResponse(**result)


@identity_router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary=CREATE_USER_SUMMARY,
    description=CREATE_USER_DESC,
)
async def create_user(
    user_in: UserCreate,
    dal: UserDAL = Depends(get_dal),
) -> UserResponse:
    """Create new user."""
    return await _create_user(user_in, dal)
