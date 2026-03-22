"""Data Access Layer for identity operations."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.v1.identity.models import User
from src.routers.v1.identity.schemas import UserCreate


class UserDAL:
    """Data Access Layer for user management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password for secure storage."""
        # TODO: Use passlib or similar for proper hashing
        # from passlib.context import CryptContext
        # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # return pwd_context.hash(password)
        return f"hashed_{password}"

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify password against hash."""
        # TODO: Use passlib for proper verification
        # from passlib.context import CryptContext
        # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # return pwd_context.verify(plain, hashed)
        return hashed == f"hashed_{plain}"

    async def create(self, user_in: UserCreate) -> dict:
        """Create new user with hashed password."""
        new_user = User(
            username=user_in.username,
            email=user_in.email,
            password_hash=self.hash_password(user_in.password),
            is_active=True,
        )
        self.session.add(new_user)
        await self.session.flush()
        return new_user.to_dict() | {"id": new_user.id}

    async def get_by_username(self, username: str) -> dict | None:
        """Get user by username."""
        stmt = select(User).where(User.username == username, User.is_active == True)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user_dict = user.to_dict()
            user_dict["password_hash"] = user.password_hash
            return user_dict
        return None

    async def get_by_email(self, email: str) -> dict | None:
        """Get user by email."""
        stmt = select(User).where(User.email == email, User.is_active == True)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.to_dict() | {"id": user.id} if user else None

    async def get_by_id(self, user_id: int) -> dict | None:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id, User.is_active == True)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        return user.to_dict() | {"id": user.id} if user else None

    async def list_users(self, skip: int = 0, limit: int = 50) -> list[dict]:
        """List active users with pagination."""
        stmt = (
            select(User)
            .where(User.is_active == True)
            .order_by(User.id.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        return [u.to_dict() | {"id": u.id} for u in users]

    async def count_users(self) -> int:
        """Count active users."""
        stmt = select(func.count(User.id)).where(User.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
