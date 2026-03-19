import os
from abc import ABC
from dataclasses import asdict, dataclass


class CfgBase(ABC):
    dict: callable = asdict


@dataclass
class RedisCfg(CfgBase):
    """Redis configuration for token blacklist, rate limiting, and active sessions."""
    host: str = os.getenv("REDIS_HOST")
    port: int = os.getenv("REDIS_PORT")
    db: int = os.getenv("REDIS_DB")
    password: str = os.getenv("REDIS_PASSWORD")


@dataclass
class PostgresCfg(CfgBase):
    """PostgreSQL configuration for identity service."""
    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = os.getenv("POSTGRES_PORT", "5432")
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
