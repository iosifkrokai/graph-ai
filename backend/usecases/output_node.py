"""Usecase logic for output nodes."""

from sqlalchemy.ext.asyncio import AsyncSession

from enums import NodeType
from exceptions import ConflictError, ResourceNotFoundError
from repositories import NodeRepository, OutputNodeRepository
from schemas import OutputNodeCreate, OutputNodeResponse, OutputNodeUpdate


class OutputNodeUsecase:
    """Usecase operations for output node configurations."""

    def __init__(self) -> None:
        """Initialize repositories for output node operations."""
        self._output_repository = OutputNodeRepository()
        self._node_repository = NodeRepository()

    async def create_output_node(
        self, session: AsyncSession, data: OutputNodeCreate
    ) -> OutputNodeResponse:
        """Create an output node configuration."""
        node = await self._node_repository.get_by(session=session, id=data.node_id)
        if not node:
            resource = "Node"
            raise ResourceNotFoundError(resource)
        if node.type != NodeType.OUTPUT:
            message = "Node type is not OUTPUT"
            raise ConflictError(message)

        existing = await self._output_repository.get_by(
            session=session, node_id=data.node_id
        )
        if existing:
            message = "Output node config already exists"
            raise ConflictError(message)

        output_node = await self._output_repository.create(
            session=session,
            data={"node_id": data.node_id, "format": data.format},
        )
        return OutputNodeResponse.model_validate(output_node)

    async def get_output_node(
        self, session: AsyncSession, node_id: int
    ) -> OutputNodeResponse:
        """Fetch an output node configuration by node ID."""
        output_node = await self._output_repository.get_by(
            session=session, node_id=node_id
        )
        if not output_node:
            resource = "Output node"
            raise ResourceNotFoundError(resource)
        return OutputNodeResponse.model_validate(output_node)

    async def update_output_node(
        self, session: AsyncSession, node_id: int, data: OutputNodeUpdate
    ) -> OutputNodeResponse:
        """Update an output node configuration by node ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_output_node(session=session, node_id=node_id)

        output_node = await self._output_repository.update_by(
            session=session,
            data=update_data,
            node_id=node_id,
        )
        if not output_node:
            resource = "Output node"
            raise ResourceNotFoundError(resource)
        return OutputNodeResponse.model_validate(output_node)

    async def delete_output_node(self, session: AsyncSession, node_id: int) -> None:
        """Delete an output node configuration by node ID."""
        deleted = await self._output_repository.delete_by(
            session=session, node_id=node_id
        )
        if not deleted:
            resource = "Output node"
            raise ResourceNotFoundError(resource)
