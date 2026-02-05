"""Shared test helpers and base classes."""

from http import HTTPStatus

import pytest_asyncio
from httpx import AsyncClient, Response
from sqlalchemy.ext.asyncio import AsyncSession


class BaseTestCase:
    """Base test case with shared fixtures and assertions."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, test_session: AsyncSession, test_client: AsyncClient) -> None:
        """Attach the test session and client to the instance."""
        self.session = test_session
        self.client = test_client

    async def assert_response_ok(self, response: Response) -> dict:
        """Assert a response has an OK/ACCEPTED status and return JSON."""
        if response.status_code not in {HTTPStatus.OK, HTTPStatus.ACCEPTED}:
            message = (
                f"Expected response status OK or ACCEPTED, got {response.status_code}"
            )
            raise AssertionError(message)
        return response.json()

    async def assert_response_stream(self, response: Response) -> None:
        """Assert a streaming text response with a non-empty payload."""
        if response.status_code != HTTPStatus.OK:
            message = f"Expected response status OK, got {response.status_code}"
            raise AssertionError(message)
        if response.headers.get("content-type") != "text/plain; charset=utf-8":
            message = "Expected text/plain response content type"
            raise AssertionError(message)
        content = b""
        async for chunk in response.aiter_bytes():
            content += chunk
        if not isinstance(content, bytes):
            message = "Expected streamed content to be bytes"
            raise TypeError(message)
        if len(content) == 0:
            message = "Expected streamed content to be non-empty"
            raise AssertionError(message)
