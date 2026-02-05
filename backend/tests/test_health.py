"""Tests for health endpoints."""

from http import HTTPStatus

import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_liveness() -> None:
    """Ensure the liveness endpoint returns a healthy response."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health/liveness")

    if response.status_code != HTTPStatus.OK:
        message = f"Expected status {HTTPStatus.OK}, got {response.status_code}"
        raise AssertionError(message)
    if response.json() != {"status": True}:
        message = "Expected liveness response payload to be healthy"
        raise AssertionError(message)
