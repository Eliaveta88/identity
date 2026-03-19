"""Data Access Layer for identity operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.v1.identity.schemas import UserCreate


class UserDAL:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_in: UserCreate) -> dict:
        return {"id": 1, **user_in.model_dump(exclude={"password"})}

    async def get_by_username(self, username: str) -> dict | None:
        return None

    async def get_by_id(self, user_id: int) -> dict | None:
        return None
