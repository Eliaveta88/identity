import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from src.routers.v1.identity.actions import _login, _logout
from src.routers.v1.identity.schemas import LoginRequest
from src.config import redis_cfg
from src.services import redis as redis_service


class IdentityRedisIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def test_redis_cfg_hardening_fields_present(self) -> None:
        self.assertGreater(redis_cfg.socket_timeout_seconds, 0)
        self.assertGreater(redis_cfg.socket_connect_timeout_seconds, 0)
        self.assertGreater(redis_cfg.health_check_interval_seconds, 0)
        self.assertGreater(redis_cfg.max_connections, 0)

    async def test_get_redis_uses_from_url_with_hardening_kwargs(self) -> None:
        redis_service._pool = None
        fake_client = AsyncMock()
        with patch(
            "src.services.redis.aioredis.from_url",
            return_value=fake_client,
        ) as from_url_mock:
            client = await redis_service.get_redis()
        self.assertIs(client, fake_client)
        from_url_mock.assert_called_once_with(
            redis_cfg.url,
            decode_responses=redis_cfg.decode_responses,
            socket_timeout=redis_cfg.socket_timeout_seconds,
            socket_connect_timeout=redis_cfg.socket_connect_timeout_seconds,
            health_check_interval=redis_cfg.health_check_interval_seconds,
            max_connections=redis_cfg.max_connections,
        )
        redis_service._pool = None

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
