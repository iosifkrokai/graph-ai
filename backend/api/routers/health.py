"""Health check API routes."""

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.dependencies import health
from schemas import HealthResponse, ServiceHealthResponse
from usecases import HealthUsecase

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(path="/liveness")
async def liveness() -> JSONResponse:
    """Return a basic liveness response."""
    return JSONResponse(content={"status": True})


@router.get(path="/readiness")
async def readiness(
    usecase: Annotated[HealthUsecase, Depends(health.get_health_usecase)],
) -> JSONResponse:
    """Return readiness status for downstream services.

    Responds 503 (instead of 200) once any dependency is unhealthy, so a
    load balancer or orchestrator can actually act on this check.
    """
    health = await usecase.health()
    response = HealthResponse(
        services=[
            ServiceHealthResponse(name=name, status=status)
            for name, status in health.items()
        ]
    )
    status_code = HTTPStatus.OK if response.status else HTTPStatus.SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code, content=response.model_dump(mode="json")
    )
