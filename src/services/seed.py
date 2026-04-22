"""Initial data seeding for identity service."""

from __future__ import annotations

import logging
import os

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.v1.identity.dal import UserDAL
from src.routers.v1.identity.models import User

logger = logging.getLogger(__name__)

_DEFAULT_ADMIN_EMAIL = "admin@local.dev"
_email_adapter = TypeAdapter(EmailStr)


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


def _validated_admin_email(raw: str) -> str:
    """Return an email valid for Pydantic ``EmailStr`` in API responses."""
    try:
        return str(_email_adapter.validate_python(raw))
    except Exception:
        logger.warning(
            "ADMIN_EMAIL %r is not valid for API EmailStr; using %r",
            raw,
            _DEFAULT_ADMIN_EMAIL,
        )
        return _DEFAULT_ADMIN_EMAIL


async def ensure_initial_admin(session: AsyncSession) -> None:
    """Create the first admin user if the ``users`` table is empty.

    Credentials are taken from ``ADMIN_USERNAME`` / ``ADMIN_PASSWORD`` /
    ``ADMIN_EMAIL`` env vars (defaults: ``admin`` / ``admin`` /
    ``admin@local.dev``). No-op if any user already exists.
    """

    total = await session.scalar(select(func.count(User.id)))
    if total:
        return

    username = _env("ADMIN_USERNAME", "admin")
    password = _env("ADMIN_PASSWORD", "admin")
    email = _validated_admin_email(_env("ADMIN_EMAIL", _DEFAULT_ADMIN_EMAIL))

    admin = User(
        username=username,
        email=email,
        password_hash=UserDAL.hash_password(password),
        is_active=True,
        is_superuser=True,
    )
    session.add(admin)
    await session.flush()
    logger.info("Seeded initial admin user '%s' (id=%s)", username, admin.id)
