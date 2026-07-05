"""Health dependency providers."""

from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from api.dependencies import db
from api.dependencies.qdrant import get_qdrant_client
from api.dependencies.redis import get_redis_client
from usecases import HealthUsecase


def get_health_usecase(
    redis_client: Annotated[Redis, Depends(get_redis_client)],
    session_factory: Annotated[
        async_sessionmaker[AsyncSession], Depends(db.get_session_factory)
    ],
    qdrant_client: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> HealthUsecase:
    """Get the health usecase.

    Args:
        redis_client: The shared Redis client.
        session_factory: Factory for a short-lived DB session.
        qdrant_client: The Qdrant client.

    Returns:
        The health usecase.

    """
    return HealthUsecase(
        redis_client=redis_client,
        session_factory=session_factory,
        qdrant_client=qdrant_client,
    )
