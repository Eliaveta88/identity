"""Identity v1 endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.core import get_async_session
from src.dependencies import TokenPayload, get_access_token_payload, get_current_user_id
from src.routers.v1.identity.actions import (
    _create_user,
    _get_current_user,
    _get_user_by_id,
    _list_users,
    _login,
    _logout,
    _logout_all,
    _refresh_tokens,
)
from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.description import (
    CREATE_USER_DESC,
    GET_CURRENT_USER_DESC,
    LOGIN_DESC,
    LOGOUT_ALL_DESC,
    LOGOUT_DESC,
    REFRESH_TOKEN_DESC,
)
from src.routers.v1.identity.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshTokenRequest,
    UserCreate,
    UserListResponse,
    UserResponse,
)
from src.routers.v1.identity.summary import (
    CREATE_USER_SUMMARY,
    GET_CURRENT_USER_SUMMARY,
    LOGIN_SUMMARY,
    LOGOUT_ALL_SUMMARY,
    LOGOUT_SUMMARY,
    REFRESH_TOKEN_SUMMARY,
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
    "/refresh",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary=REFRESH_TOKEN_SUMMARY,
    description=REFRESH_TOKEN_DESC,
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    dal: UserDAL = Depends(get_dal),
) -> LoginResponse:
    """Exchange refresh token for new access + refresh tokens."""
    return await _refresh_tokens(body, dal)


@identity_router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary=LOGOUT_SUMMARY,
    description=LOGOUT_DESC,
)
async def logout(
    payload: Annotated[TokenPayload, Depends(get_access_token_payload)],
    dal: UserDAL = Depends(get_dal),
) -> LogoutResponse:
    """Logout user (requires Bearer access token)."""
    result = await _logout(payload, dal)
    return LogoutResponse(**result)


@identity_router.get(
    "/users/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary=GET_CURRENT_USER_SUMMARY,
    description=GET_CURRENT_USER_DESC,
)
async def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    dal: UserDAL = Depends(get_dal),
) -> UserResponse:
    """Get current user."""
    return await _get_current_user(user_id, dal)


@identity_router.post(
    "/logout-all",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary=LOGOUT_ALL_SUMMARY,
    description=LOGOUT_ALL_DESC,
)
async def logout_all(
    user_id: Annotated[int, Depends(get_current_user_id)],
    dal: UserDAL = Depends(get_dal),
) -> LogoutResponse:
    """Logout user from all sessions."""
    result = await _logout_all(user_id, dal)
    return LogoutResponse(**result)


@identity_router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Пользователь по id",
    description="Профиль по id (интеграция заказов, логистики).",
)
async def get_user_by_id(
    user_id: Annotated[int, Path(..., gt=0, description="User ID")],
    dal: UserDAL = Depends(get_dal),
) -> UserResponse:
    return await _get_user_by_id(user_id, dal)


@identity_router.get(
    "/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="Список пользователей",
    description="Активные пользователи с пагинацией (для админки).",
)
async def list_users(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    dal: UserDAL = Depends(get_dal),
) -> UserListResponse:
    return await _list_users(dal, skip=skip, limit=limit)


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
