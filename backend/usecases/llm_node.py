"""Usecase logic for LLM nodes."""

from sqlalchemy.ext.asyncio import AsyncSession

from enums import NodeType
from exceptions import ConflictError, ResourceNotFoundError
from repositories import LLMNodeRepository, LLMProviderRepository, NodeRepository
from schemas import LLMNodeCreate, LLMNodeResponse, LLMNodeUpdate


class LLMNodeUsecase:
    """Usecase operations for LLM node configurations."""

    def __init__(self) -> None:
        """Initialize repositories for LLM node operations."""
        self._llm_repository = LLMNodeRepository()
        self._node_repository = NodeRepository()
        self._provider_repository = LLMProviderRepository()

    async def create_llm_node(
        self, session: AsyncSession, data: LLMNodeCreate
    ) -> LLMNodeResponse:
        """Create an LLM node configuration."""
        node = await self._node_repository.get_by(session=session, id=data.node_id)
        if not node:
            resource = "Node"
            raise ResourceNotFoundError(resource)
        if node.type != NodeType.LLM:
            message = "Node type is not LLM"
            raise ConflictError(message)

        provider = await self._provider_repository.get_by(
            session=session, id=data.llm_provider_id
        )
        if not provider:
            resource = "LLM provider"
            raise ResourceNotFoundError(resource)

        existing = await self._llm_repository.get_by(
            session=session, node_id=data.node_id
        )
        if existing:
            message = "LLM node config already exists"
            raise ConflictError(message)

        llm_node = await self._llm_repository.create(
            session=session,
            data={
                "node_id": data.node_id,
                "llm_provider_id": data.llm_provider_id,
                "model": data.model,
                "temperature": data.temperature,
                "max_tokens": data.max_tokens,
            },
        )
        return LLMNodeResponse.model_validate(llm_node)

    async def get_llm_node(
        self, session: AsyncSession, node_id: int
    ) -> LLMNodeResponse:
        """Fetch an LLM node configuration by node ID."""
        llm_node = await self._llm_repository.get_by(session=session, node_id=node_id)
        if not llm_node:
            resource = "LLM node"
            raise ResourceNotFoundError(resource)
        return LLMNodeResponse.model_validate(llm_node)

    async def update_llm_node(
        self, session: AsyncSession, node_id: int, data: LLMNodeUpdate
    ) -> LLMNodeResponse:
        """Update an LLM node configuration by node ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_llm_node(session=session, node_id=node_id)

        if "llm_provider_id" in update_data:
            provider = await self._provider_repository.get_by(
                session=session, id=update_data["llm_provider_id"]
            )
            if not provider:
                resource = "LLM provider"
                raise ResourceNotFoundError(resource)

        llm_node = await self._llm_repository.update_by(
            session=session,
            data=update_data,
            node_id=node_id,
        )
        if not llm_node:
            resource = "LLM node"
            raise ResourceNotFoundError(resource)
        return LLMNodeResponse.model_validate(llm_node)

    async def delete_llm_node(self, session: AsyncSession, node_id: int) -> None:
        """Delete an LLM node configuration by node ID."""
        deleted = await self._llm_repository.delete_by(session=session, node_id=node_id)
        if not deleted:
            resource = "LLM node"
            raise ResourceNotFoundError(resource)
