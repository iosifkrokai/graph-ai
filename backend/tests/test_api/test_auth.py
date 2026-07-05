"""Auth API tests."""

import secrets
import uuid
from http import HTTPStatus

import pytest
from jose import jwt

from db.repositories import LLMProviderRepository
from enums import LLMProviderType
from settings import auth_settings
from tests.factories import UserFactory
from tests.test_api.base import BaseTestCase
from utils.crypto import hash_password


class TestAuthRegister(BaseTestCase):
    """Tests for POST /auth/register."""

    url = "/auth/register"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful registration returns user data."""
        payload = {
            "email": f"john.doe-{uuid.uuid4().hex[:8]}@example.com",
            "password": secrets.token_urlsafe(16),
        }

        response = await self.client.post(url=self.url, json=payload)

        data = await self.assert_response_dict(response=response)
        self.assert_has_keys(data, {"id", "email", "created_at", "updated_at"})
        if data["email"] != payload["email"]:
            pytest.fail("Response email did not match request")
        if "hashed_password" in data:
            pytest.fail("Response must not include 'hashed_password'")
        if "password" in data:
            pytest.fail("Response must not include 'password'")

    @pytest.mark.asyncio
    async def test_creates_default_ollama_provider(self) -> None:
        """Registration creates a default local Ollama provider."""
        payload = {
            "email": f"john.doe-{uuid.uuid4().hex[:8]}@example.com",
            "password": secrets.token_urlsafe(16),
        }

        response = await self.client.post(url=self.url, json=payload)
        data = await self.assert_response_dict(response=response)

        providers = await LLMProviderRepository().get_all(
            session=self.session, user_id=data["id"]
        )

        if len(providers) != 1:
            pytest.fail("Expected exactly one default LLM provider for new user")

        provider = providers[0]
        if provider.type != LLMProviderType.OLLAMA:
            pytest.fail("Expected default provider type to be OLLAMA")
        if provider.name != "ollama":
            pytest.fail("Expected default provider name to be 'ollama'")

    @pytest.mark.asyncio
    async def test_short_password_rejected(self) -> None:
        """A password under 8 characters is rejected."""
        payload = {
            "email": f"john.doe-{uuid.uuid4().hex[:8]}@example.com",
            "password": "short1",
        }

        response = await self.client.post(url=self.url, json=payload)

        if response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY:
            pytest.fail(f"Expected a validation error, got {response.status_code}")

    @pytest.mark.asyncio
    async def test_long_password_rejected(self) -> None:
        """A password over 72 characters is rejected."""
        payload = {
            "email": f"john.doe-{uuid.uuid4().hex[:8]}@example.com",
            "password": "x" * 73,
        }

        response = await self.client.post(url=self.url, json=payload)

        if response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY:
            pytest.fail(f"Expected a validation error, got {response.status_code}")


class TestAuthLogin(BaseTestCase):
    """Tests for POST /auth/login."""

    url = "/auth/login"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful login returns access token."""
        user_data = {
            "email": f"john.doe-{uuid.uuid4().hex[:8]}@example.com",
            "password": secrets.token_urlsafe(16),
        }
        await UserFactory.create_async(
            session=self.session,
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
        )

        response = await self.client.post(
            url=self.url,
            json={"email": user_data["email"], "password": user_data["password"]},
        )

        data = await self.assert_response_dict(response=response)
        self.assert_has_keys(data, {"access_token", "token_type"})
        if data["token_type"] != auth_settings.token_type:
            pytest.fail("Token type did not match expected value")

    @pytest.mark.asyncio
    async def test_token_includes_iat_and_jti(self) -> None:
        """The issued access token carries iat/jti claims."""
        user_data = {
            "email": f"john.doe-{uuid.uuid4().hex[:8]}@example.com",
            "password": secrets.token_urlsafe(16),
        }
        await UserFactory.create_async(
            session=self.session,
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
        )

        response = await self.client.post(
            url=self.url,
            json={"email": user_data["email"], "password": user_data["password"]},
        )
        data = await self.assert_response_dict(response=response)

        payload = jwt.decode(
            token=data["access_token"],
            key=auth_settings.secret_key,
            algorithms=[auth_settings.algorithm],
        )
        self.assert_has_keys(payload, {"exp", "iat", "jti", "sub"})
