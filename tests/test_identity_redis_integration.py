import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.routers.v1.identity.actions import _login, _logout
from src.routers.v1.identity.schemas import LoginRequest


class IdentityRedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_rate_limited_returns_429(self) -> None:
        dal = AsyncMock()
        credentials = LoginRequest(username="demo", password="secret")
        with patch(
            "src.routers.v1.identity.actions.check_rate_limit",
            new=AsyncMock(return_value=(False, 6)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await _login(credentials, dal)
        self.assertEqual(ctx.exception.status_code, 429)

    async def test_logout_blacklists_and_revokes_session(self) -> None:
        dal = AsyncMock()
        with (
            patch(
                "src.routers.v1.identity.actions.blacklist_token",
                new=AsyncMock(),
            ) as blacklist_mock,
            patch(
                "src.routers.v1.identity.actions.revoke_session",
                new=AsyncMock(),
            ) as revoke_mock,
        ):
            result = await _logout(
                user_id=1,
                dal=dal,
                token_jti="jti-1",
                session_id="sess-1",
            )
        self.assertEqual(result["status"], "ok")
        blacklist_mock.assert_awaited_once()
        revoke_mock.assert_awaited_once()
