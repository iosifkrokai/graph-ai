"""Health endpoint tests."""

from http import HTTPStatus

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from api.dependencies import redis as redis_dependency
from main import app
from tests.test_api.base import BaseTestCase


class TestHealthLiveness(BaseTestCase):
    """Liveness checks for the health endpoint."""

    url = "/health/liveness"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Returns a healthy status for liveness checks."""
        response = await self.client.get(url=self.url)

        data = await self.assert_response_ok(response=response)
        if data.get("status") is not True:
            pytest.fail("Expected liveness status to be true")


class TestHealthReadiness(BaseTestCase):
    """Readiness checks for the health endpoint."""

    url = "/health/readiness"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Returns 200 with all services healthy when dependencies are up."""
        response = await self.client.get(url=self.url)

        data = await self.assert_response_dict(response=response)
        self.assert_has_keys(data, {"services", "status"})
        if not isinstance(data["services"], list):
            pytest.fail("Expected services to be a list")
        if data["status"] is not True:
            pytest.fail("Expected overall status to be healthy")

        checked = {service["name"] for service in data["services"]}
        if checked != {"postgres", "redis", "qdrant"}:
            pytest.fail(f"Expected postgres/redis/qdrant to be checked, got {checked}")

    @pytest.mark.asyncio
    async def test_unhealthy_dependency_returns_503(self) -> None:
        """Responds 503 (not 200) once a dependency check fails."""

        class _BrokenRedisClient:
            async def ping(self) -> bool:
                message = "connection refused"
                raise RedisConnectionError(message)

        previous = app.dependency_overrides[redis_dependency.get_redis_client]
        app.dependency_overrides[redis_dependency.get_redis_client] = _BrokenRedisClient
        try:
            response = await self.client.get(url=self.url)
        finally:
            app.dependency_overrides[redis_dependency.get_redis_client] = previous

        if response.status_code != HTTPStatus.SERVICE_UNAVAILABLE:
            message = (
                f"Expected 503 when a dependency is down, got {response.status_code}"
            )
            pytest.fail(message)

        data = response.json()
        if data["status"] is not False:
            pytest.fail("Expected overall status to be unhealthy")
