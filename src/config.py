import os
from abc import ABC
from dataclasses import asdict, dataclass


class CfgBase(ABC):
    dict: callable = asdict


@dataclass
class RedisCfg(CfgBase):
    """Redis configuration for token blacklist, rate limiting, and active sessions."""

    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: str = os.getenv("REDIS_PASSWORD", "")
    decode_responses: bool = True
    socket_timeout_seconds: float = float(os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "3"))
    socket_connect_timeout_seconds: float = float(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "3"))
    health_check_interval_seconds: int = int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL_SECONDS", "30"))
    max_connections: int = int(os.getenv("REDIS_MAX_CONNECTIONS", "100"))

    @property
    def url(self) -> str:
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


@dataclass
class PostgresCfg(CfgBase):
    """PostgreSQL configuration for identity service."""

    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    user: str = os.getenv("POSTGRES_USER", "user")
    password: str = os.getenv("POSTGRES_PASSWORD", "pass")
    db_name: str = os.getenv("POSTGRES_DB", "identity")


@dataclass
class JWTCfg(CfgBase):
    """JWT token configuration for access and refresh tokens."""

    jwt_secret: str = os.getenv("JWT_SECRET")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_exp: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")


redis_cfg = RedisCfg()
postgres_cfg = PostgresCfg()
jwt_cfg = JWTCfg()
