"""Redis service for identity: token blacklist, rate limiting, active sessions."""

from __future__ import annotations

import redis.asyncio as aioredis

from src.config import redis_cfg

_KEY_PREFIX = "identity"
_TOKEN_BLACKLIST = f"{_KEY_PREFIX}:blacklist:"
_RATE_LIMIT = f"{_KEY_PREFIX}:rate:"
_SESSION = f"{_KEY_PREFIX}:session:"

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return the shared async Redis connection (lazy-init)."""
    global _pool
    if _pool is None:
        _pool = aioredis.Redis(
            host=redis_cfg.host,
            port=redis_cfg.port,
            db=redis_cfg.db,
            password=redis_cfg.password or None,
            decode_responses=redis_cfg.decode_responses,
        )
    return _pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


# ---------------------------------------------------------------------------
# Token blacklist
# ---------------------------------------------------------------------------


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JWT token ID to the blacklist with a TTL matching the token's
    remaining lifetime so it auto-expires when the token would have expired."""
    r = await get_redis()
    await r.set(f"{_TOKEN_BLACKLIST}{jti}", "1", ex=ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a token has been revoked."""
    r = await get_redis()
    return await r.exists(f"{_TOKEN_BLACKLIST}{jti}") > 0


# ---------------------------------------------------------------------------
# Rate limiting  (sliding-window counter)
# ---------------------------------------------------------------------------


async def check_rate_limit(
    key: str,
    max_attempts: int = 5,
    window_seconds: int = 300,
) -> tuple[bool, int]:
    """Increment the counter for *key* and return (allowed, current_count).

    Uses a simple fixed-window counter stored as a Redis key with TTL.
    Returns ``(True, count)`` when under the limit, ``(False, count)`` otherwise.
    """
    r = await get_redis()
    redis_key = f"{_RATE_LIMIT}{key}"

    pipe = r.pipeline(transaction=True)
    pipe.incr(redis_key)
    pipe.ttl(redis_key)
    count, ttl = await pipe.execute()

    if ttl == -1:
        await r.expire(redis_key, window_seconds)

    return count <= max_attempts, count


async def reset_rate_limit(key: str) -> None:
    """Reset rate-limit counter (e.g. after a successful login)."""
    r = await get_redis()
    await r.delete(f"{_RATE_LIMIT}{key}")


# ---------------------------------------------------------------------------
# Active sessions
# ---------------------------------------------------------------------------


async def register_session(
    user_id: int,
    session_id: str,
    ttl_seconds: int,
) -> None:
    """Register an active session for a user."""
    r = await get_redis()
    user_key = f"{_SESSION}{user_id}"
    await r.sadd(user_key, session_id)
    await r.expire(user_key, ttl_seconds)


async def get_active_sessions(user_id: int) -> set[str]:
    """Return all active session IDs for a user."""
    r = await get_redis()
    return await r.smembers(f"{_SESSION}{user_id}")


async def revoke_session(user_id: int, session_id: str) -> None:
    """Remove a single session from the active set."""
    r = await get_redis()
    await r.srem(f"{_SESSION}{user_id}", session_id)


async def revoke_all_sessions(user_id: int) -> None:
    """Force-logout: remove all sessions for a user."""
    r = await get_redis()
    await r.delete(f"{_SESSION}{user_id}")
