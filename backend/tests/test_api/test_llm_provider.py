"""LLM provider API tests."""

import uuid
from http import HTTPStatus

import pytest

from db.repositories import LLMProviderRepository
from enums import LLMProviderType
from tests.factories import LLMProviderFactory, UserFactory
from tests.test_api.base import BaseTestCase
from utils.encryption import decrypt


class TestLLMProviderCreate(BaseTestCase):
    """Tests for POST /llm-providers."""

    url = "/llm-providers"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful creation returns provider data."""
        user, headers = await self.create_user_and_get_token()
        payload = {
            "name": f"provider-{uuid.uuid4().hex[:8]}",
            "type": LLMProviderType.OLLAMA,
            "base_url": "https://example.com",
            "config": {"timeout": 5},
        }

        response = await self.client.post(url=self.url, json=payload, headers=headers)

        data = await self.assert_response_dict(response=response)
        self.assert_has_keys(
            data,
            {"id", "user_id", "name", "type", "base_url"},
        )
        if data["name"] != payload["name"]:
            pytest.fail("Provider name did not match request")
        if data["type"] != payload["type"]:
            pytest.fail("Provider type did not match request")
        if data["user_id"] != user["id"]:
            pytest.fail("Provider user_id did not match current user")
        if data["config"] != payload["config"]:
            pytest.fail("Provider config did not match request")

    @pytest.mark.asyncio
    async def test_api_key_stored_encrypted_and_not_returned(self) -> None:
        """A provided API key is encrypted at rest and never returned."""
        _, headers = await self.create_user_and_get_token()
        plaintext = "sk-super-secret-key"
        payload = {
            "name": f"provider-{uuid.uuid4().hex[:8]}",
            "type": LLMProviderType.OLLAMA,
            "base_url": "https://example.com",
            "api_key": plaintext,
        }

        response = await self.client.post(url=self.url, json=payload, headers=headers)

        data = await self.assert_response_dict(response=response)
        if "api_key" in data:
            pytest.fail("API key must never appear in the response")

        stored = await LLMProviderRepository().get_by(
            session=self.session, id=data["id"]
        )
        if stored is None or stored.api_key is None:
            pytest.fail("Expected the provider to persist an API key")
        elif stored.api_key == plaintext:
            pytest.fail("API key must be stored encrypted, not as plaintext")
        elif decrypt(stored.api_key) != plaintext:
            pytest.fail("Stored API key must decrypt back to the original value")

    @pytest.mark.asyncio
    async def test_oversized_config_rejected(self) -> None:
        """A config dict that serializes too large is rejected."""
        _, headers = await self.create_user_and_get_token()
        payload = {
            "name": f"provider-{uuid.uuid4().hex[:8]}",
            "type": LLMProviderType.OLLAMA,
            "base_url": "https://example.com",
            "config": {"blob": "x" * 10_000},
        }

        response = await self.client.post(url=self.url, json=payload, headers=headers)

        if response.status_code != HTTPStatus.UNPROCESSABLE_ENTITY:
            pytest.fail(f"Expected a validation error, got {response.status_code}")

    @pytest.mark.asyncio
    async def test_duplicate_name_rejected(self) -> None:
        """Creating two providers with the same name for one user returns 409."""
        _, headers = await self.create_user_and_get_token()
        payload = {
            "name": f"provider-{uuid.uuid4().hex[:8]}",
            "type": LLMProviderType.OLLAMA,
            "base_url": "https://example.com",
        }

        first_response = await self.client.post(
            url=self.url, json=payload, headers=headers
        )
        await self.assert_response_dict(response=first_response)

        second_response = await self.client.post(
            url=self.url, json=payload, headers=headers
        )

        if second_response.status_code != HTTPStatus.CONFLICT:
            pytest.fail(
                f"Expected 409 for a duplicate name, got {second_response.status_code}"
            )


class TestLLMProviderList(BaseTestCase):
    """Tests for GET /llm-providers."""

    url = "/llm-providers"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """List returns providers for the current user only."""
        user, headers = await self.create_user_and_get_token()
        other = await UserFactory.create_async(session=self.session)

        first = await LLMProviderFactory.create_async(
            session=self.session, user_id=user["id"]
        )
        second = await LLMProviderFactory.create_async(
            session=self.session, user_id=user["id"]
        )
        other_provider = await LLMProviderFactory.create_async(
            session=self.session, user_id=other.id
        )

        response = await self.client.get(url=self.url, headers=headers)

        data = await self.assert_response_list(response=response)
        ids = {item.get("id") for item in data}
        if first.id not in ids or second.id not in ids:
            pytest.fail("Expected providers to appear in list")
        if other_provider.id in ids:
            pytest.fail("Unexpected provider from another user in list")


class TestLLMProviderUpdate(BaseTestCase):
    """Tests for PATCH /llm-providers/{provider_id}."""

    url = "/llm-providers"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful update returns updated provider data."""
        user, headers = await self.create_user_and_get_token()
        provider = await LLMProviderFactory.create_async(
            session=self.session, user_id=user["id"]
        )
        new_name = f"provider-{uuid.uuid4().hex[:8]}"

        response = await self.client.patch(
            url=f"{self.url}/{provider.id}",
            json={"name": new_name},
            headers=headers,
        )

        data = await self.assert_response_dict(response=response)
        if data["name"] != new_name:
            pytest.fail("Provider name was not updated")


class TestLLMProviderDelete(BaseTestCase):
    """Tests for DELETE /llm-providers/{provider_id}."""

    url = "/llm-providers"

    @pytest.mark.asyncio
    async def test_ok(self) -> None:
        """Successful delete removes the provider."""
        user, headers = await self.create_user_and_get_token()
        provider = await LLMProviderFactory.create_async(
            session=self.session, user_id=user["id"]
        )

        response = await self.client.delete(
            url=f"{self.url}/{provider.id}",
            headers=headers,
        )

        await self.assert_response_ok(response=response)

        fetch = await self.client.get(
            url=self.url,
            headers=headers,
        )
        data = await self.assert_response_list(response=fetch)
        ids = {item.get("id") for item in data}
        if provider.id in ids:
            pytest.fail("Expected deleted provider to not appear in list")
