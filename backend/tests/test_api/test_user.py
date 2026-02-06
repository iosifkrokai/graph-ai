"""User API tests."""

import pytest

from tests.test_api.base import BaseTestCase


class TestUserMe(BaseTestCase):
    """Tests for GET /user/me."""

    url = "/user/me"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful request returns current user data."""
        user, headers = await self.create_user_and_get_token()

        response = await self.client.get(url=self.url, headers=headers)

        data = await self.assert_response_ok(response=response)
        assert data["id"] == user["id"]
        assert data["email"] == user["email"]


class TestUserMeDelete(BaseTestCase):
    """Tests for DELETE /user/me."""

    url = "/user/me"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful request deletes the current user."""
        _, headers = await self.create_user_and_get_token()

        response = await self.client.delete(url=self.url, headers=headers)

        await self.assert_response_ok(response=response)
