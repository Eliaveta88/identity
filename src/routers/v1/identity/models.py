"""SQLAlchemy ORM models for identity service."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import mapped_column

from src.database.core import Base


class User(Base):
    """User database model."""

    __tablename__ = "users"

    id: int = mapped_column(Integer, primary_key=True)
    username: str = mapped_column(String(50), nullable=False, unique=True, index=True)
    email: str = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: str = mapped_column(String(255), nullable=False)
    is_active: bool = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_superuser: bool = mapped_column(Boolean, default=False, nullable=False)
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "roles": ["superuser"] if self.is_superuser else ["user"],
            "is_active": self.is_active,
        }


class Role(Base):
    """User role database model."""

    __tablename__ = "roles"

    id: int = mapped_column(Integer, primary_key=True)
    user_id: int = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_name: str = mapped_column(
        String(50), nullable=False, index=True
    )  # admin, manager, operator, viewer
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "user_id": self.user_id,
            "role_name": self.role_name,
        }


class UserSession(Base):
    """User session database model (DB-backed sessions; JWT also uses Redis)."""

    __tablename__ = "sessions"

    id: int = mapped_column(Integer, primary_key=True)
    user_id: int = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: str = mapped_column(String(500), nullable=False, unique=True, index=True)
    refresh_token: str = mapped_column(String(500), nullable=False, unique=True, index=True)
    ip_address: str = mapped_column(String(45), nullable=True)
    user_agent: str = mapped_column(String(500), nullable=True)
    is_active: bool = mapped_column(Boolean, default=True, nullable=False, index=True)
    expires_at: datetime = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: datetime = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "user_id": self.user_id,
            "is_active": self.is_active,
            "expires_at": self.expires_at,
        }
