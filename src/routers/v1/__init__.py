"""API v1 router aggregator."""

from fastapi import APIRouter

from src.routers.v1.identity.endpoints import identity_router
from src.routers.v1.common.endpoints import common_router

v1_router = APIRouter()
v1_router.include_router(common_router)
v1_router.include_router(identity_router)
