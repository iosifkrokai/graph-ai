"""Usecase logic for LLM providers."""

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import ResourceNotFoundError
from repositories import LLMProviderRepository, UserRepository
from schemas import LLMProviderCreate, LLMProviderResponse, LLMProviderUpdate


class LLMProviderUsecase:
    """Usecase operations for LLM providers."""

    def __init__(self) -> None:
        """Initialize repositories for provider operations."""
        self._provider_repository = LLMProviderRepository()
        self._user_repository = UserRepository()

    async def create_provider(
        self, session: AsyncSession, data: LLMProviderCreate
    ) -> LLMProviderResponse:
        """Create a new LLM provider."""
        user = await self._user_repository.get_by(session=session, id=data.user_id)
        if not user:
            resource = "User"
            raise ResourceNotFoundError(resource)

        provider = await self._provider_repository.create(
            session=session,
            data={
                "user_id": data.user_id,
                "name": data.name,
                "type": data.type,
                "api_key": data.api_key,
                "base_url": data.base_url,
                "is_default": data.is_default,
            },
        )
        return LLMProviderResponse.model_validate(provider)

    async def get_providers(
        self, session: AsyncSession, user_id: int | None = None
    ) -> list[LLMProviderResponse]:
        """List LLM providers, optionally filtered by user."""
        filters = {"user_id": user_id} if user_id else {}
        return [
            LLMProviderResponse.model_validate(provider)
            for provider in await self._provider_repository.get_all(
                session=session, **filters
            )
        ]

    async def get_provider(
        self, session: AsyncSession, provider_id: int
    ) -> LLMProviderResponse:
        """Fetch an LLM provider by ID."""
        provider = await self._provider_repository.get_by(
            session=session, id=provider_id
        )
        if not provider:
            resource = "LLM provider"
            raise ResourceNotFoundError(resource)
        return LLMProviderResponse.model_validate(provider)

    async def update_provider(
        self, session: AsyncSession, provider_id: int, data: LLMProviderUpdate
    ) -> LLMProviderResponse:
        """Update an LLM provider by ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_provider(session=session, provider_id=provider_id)

        provider = await self._provider_repository.update_by(
            session=session,
            data=update_data,
            id=provider_id,
        )
        if not provider:
            resource = "LLM provider"
            raise ResourceNotFoundError(resource)
        return LLMProviderResponse.model_validate(provider)

    async def delete_provider(self, session: AsyncSession, provider_id: int) -> None:
        """Delete an LLM provider by ID."""
        deleted = await self._provider_repository.delete_by(
            session=session, id=provider_id
        )
        if not deleted:
            resource = "LLM provider"
            raise ResourceNotFoundError(resource)
