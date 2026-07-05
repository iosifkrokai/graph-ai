"""CORS middleware tests."""

import pytest

from settings import cors_settings
from tests.test_api.base import BaseTestCase


class TestCors(BaseTestCase):
    """CORS header checks on a simple request."""

    url = "/health/liveness"

    @pytest.mark.asyncio
    async def test_allowed_origin_gets_cors_header(self) -> None:
        """An allowlisted origin gets echoed back in the CORS header."""
        origin = cors_settings.origins[0]

        response = await self.client.get(url=self.url, headers={"Origin": origin})

        if response.headers.get("access-control-allow-origin") != origin:
            pytest.fail("Allowed origin did not receive a matching CORS header")

    @pytest.mark.asyncio
    async def test_disallowed_origin_gets_no_cors_header(self) -> None:
        """A non-allowlisted origin does not get a CORS header."""
        response = await self.client.get(
            url=self.url, headers={"Origin": "https://evil.example.com"}
        )

        if "access-control-allow-origin" in response.headers:
            pytest.fail("Disallowed origin should not receive a CORS header")
