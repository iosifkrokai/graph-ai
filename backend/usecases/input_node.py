"""Usecase logic for input nodes."""

from sqlalchemy.ext.asyncio import AsyncSession

from enums import NodeType
from exceptions import ConflictError, ResourceNotFoundError
from repositories import InputNodeRepository, NodeRepository
from schemas import InputNodeCreate, InputNodeResponse, InputNodeUpdate


class InputNodeUsecase:
    """Usecase operations for input node configurations."""

    def __init__(self) -> None:
        """Initialize repositories for input node operations."""
        self._input_repository = InputNodeRepository()
        self._node_repository = NodeRepository()

    async def create_input_node(
        self, session: AsyncSession, data: InputNodeCreate
    ) -> InputNodeResponse:
        """Create an input node configuration."""
        node = await self._node_repository.get_by(session=session, id=data.node_id)
        if not node:
            resource = "Node"
            raise ResourceNotFoundError(resource)
        if node.type != NodeType.INPUT:
            message = "Node type is not INPUT"
            raise ConflictError(message)

        existing = await self._input_repository.get_by(
            session=session, node_id=data.node_id
        )
        if existing:
            message = "Input node config already exists"
            raise ConflictError(message)

        input_node = await self._input_repository.create(
            session=session,
            data={"node_id": data.node_id, "format": data.format},
        )
        return InputNodeResponse.model_validate(input_node)

    async def get_input_node(
        self, session: AsyncSession, node_id: int
    ) -> InputNodeResponse:
        """Fetch an input node configuration by node ID."""
        input_node = await self._input_repository.get_by(
            session=session, node_id=node_id
        )
        if not input_node:
            resource = "Input node"
            raise ResourceNotFoundError(resource)
        return InputNodeResponse.model_validate(input_node)

    async def update_input_node(
        self, session: AsyncSession, node_id: int, data: InputNodeUpdate
    ) -> InputNodeResponse:
        """Update an input node configuration by node ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_input_node(session=session, node_id=node_id)

        input_node = await self._input_repository.update_by(
            session=session,
            data=update_data,
            node_id=node_id,
        )
        if not input_node:
            resource = "Input node"
            raise ResourceNotFoundError(resource)
        return InputNodeResponse.model_validate(input_node)

    async def delete_input_node(self, session: AsyncSession, node_id: int) -> None:
        """Delete an input node configuration by node ID."""
        deleted = await self._input_repository.delete_by(
            session=session, node_id=node_id
        )
        if not deleted:
            resource = "Input node"
            raise ResourceNotFoundError(resource)
