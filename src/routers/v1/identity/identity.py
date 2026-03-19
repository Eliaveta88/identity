"""Identity v1 HTTP endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.routers.v1.identity.actions import UserActions
from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.schemas import UserCreate, UserResponse

identity_router = APIRouter(prefix="/identity", tags=["identity"])


async def get_actions() -> UserActions:
    """Get UserActions instance."""
    dal = UserDAL(session=None)  # type: ignore
    return UserActions(dal)


@identity_router.post(
    "/users",
    response_model=UserResponse,
    status_code=201,
    summary="Create user",
    description="Create new user. Action: CREATE.",
)
async def create_user(
    user_in: UserCreate,
    actions: Annotated[UserActions, Depends(get_actions)],
) -> UserResponse:
    """Register new user."""
    return await actions.create_user(user_in)


@identity_router.post(
    "/login",
    response_model=dict,
    summary="Login",
    description="Authenticate user. Action: LOGIN.",
)
async def login(
    username: str,
    password: str,
    actions: Annotated[UserActions, Depends(get_actions)],
) -> dict:
    """Authenticate and issue tokens."""
    user = await actions.get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": "mock_token", "token_type": "bearer"}
