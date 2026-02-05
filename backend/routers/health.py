"""Health check API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from dependencies import health as health_dependency
from schemas import HealthResponse, ServiceHealthResponse
from usecases import HealthUsecase

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(path="/liveness")
async def liveness() -> JSONResponse:
    """Return a basic liveness response."""
    return JSONResponse(content={"status": True})


@router.get(path="/readiness")
async def readiness(
    usecase: Annotated[HealthUsecase, Depends(health_dependency.get_health_usecase)],
) -> HealthResponse:
    """Return readiness status for downstream services."""
    health = await usecase.health()
    return HealthResponse(
        services=[
            ServiceHealthResponse(name=name, status=status)
            for name, status in health.items()
        ]
    )
