"""Identity business logic and actions."""

from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.schemas import UserCreate, UserResponse


class UserActions:
    """Business logic for user management."""

    def __init__(self, dal: UserDAL):
        self.dal = dal

    async def create_user(self, user_in: UserCreate) -> UserResponse:
        """Create new user."""
        user = await self.dal.create(user_in)
        return UserResponse(**user)

    async def get_user_by_username(self, username: str) -> UserResponse | None:
        """Get user by username."""
        user = await self.dal.get_by_username(username)
        return UserResponse(**user) if user else None

    async def get_user(self, user_id: int) -> UserResponse | None:
        """Get user by ID."""
        user = await self.dal.get_by_id(user_id)
        return UserResponse(**user) if user else None
