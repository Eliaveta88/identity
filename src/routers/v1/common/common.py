"""Common v1 HTTP endpoints."""

from fastapi import APIRouter

from src.routers.v1.common.schemas import HealthResponse, ReadyResponse

common_router = APIRouter(tags=["common"])


@common_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="identity")


@common_router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="Readiness check",
)
async def ready() -> ReadyResponse:
    return ReadyResponse(status="ready", service="identity")
