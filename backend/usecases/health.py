"""Usecase logic for health checks."""

import asyncio

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class HealthUsecase:
    """Usecase operations for health checks."""

    def __init__(
        self,
        redis_client: Redis,
        session_factory: async_sessionmaker[AsyncSession],
        qdrant_client: AsyncQdrantClient,
    ) -> None:
        """Initialize the usecase.

        Args:
            redis_client: The shared Redis client to check connectivity on.
            session_factory: Factory for a short-lived DB session.
            qdrant_client: The Qdrant client to check connectivity on.

        """
        self._redis_client = redis_client
        self._session_factory = session_factory
        self._qdrant_client = qdrant_client

    async def check_postgres(self) -> bool:
        """Check postgres connectivity.

        Returns:
            True if postgres is healthy, False otherwise.

        """
        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))
                return True
        except SQLAlchemyError:
            return False

    async def check_redis(self) -> bool:
        """Check Redis connectivity.

        Returns:
            True if Redis is healthy, False otherwise.

        """
        try:
            return bool(await self._redis_client.ping())
        except RedisError:
            return False

    async def check_qdrant(self) -> bool:
        """Check Qdrant connectivity.

        Returns:
            True if Qdrant is healthy, False otherwise.

        """
        try:
            await self._qdrant_client.get_collections()
        except (UnexpectedResponse, ResponseHandlingException, OSError):
            return False
        else:
            return True

    async def health(self) -> dict[str, bool]:
        """Check all services concurrently.

        Returns:
            Dictionary of service names and their health status.

        """
        tasks = [
            ("postgres", self.check_postgres()),
            ("redis", self.check_redis()),
            ("qdrant", self.check_qdrant()),
        ]

        results = await asyncio.gather(
            *[task[1] for task in tasks], return_exceptions=True
        )

        service_checks = {}
        for service_name, result in zip(
            [task[0] for task in tasks], results, strict=False
        ):
            if isinstance(result, Exception):
                service_checks[service_name] = False
            else:
                service_checks[service_name] = result

        return service_checks
