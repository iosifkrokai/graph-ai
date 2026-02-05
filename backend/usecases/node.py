"""Usecase logic for nodes."""

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import ResourceNotFoundError
from repositories import NodeRepository, WorkflowRepository
from schemas import NodeCreate, NodeResponse, NodeUpdate


class NodeUsecase:
    """Usecase operations for nodes."""

    def __init__(self) -> None:
        """Initialize repositories for node operations."""
        self._node_repository = NodeRepository()
        self._workflow_repository = WorkflowRepository()

    async def create_node(
        self, session: AsyncSession, data: NodeCreate
    ) -> NodeResponse:
        """Create a node within a workflow."""
        workflow = await self._workflow_repository.get_by(
            session=session, id=data.workflow_id
        )
        if not workflow:
            resource = "Workflow"
            raise ResourceNotFoundError(resource)

        node = await self._node_repository.create(
            session=session,
            data={
                "workflow_id": data.workflow_id,
                "type": data.type,
                "position_x": data.position_x,
                "position_y": data.position_y,
            },
        )
        return NodeResponse.model_validate(node)

    async def get_nodes(
        self, session: AsyncSession, workflow_id: int | None = None
    ) -> list[NodeResponse]:
        """List nodes, optionally filtered by workflow."""
        filters = {"workflow_id": workflow_id} if workflow_id else {}
        return [
            NodeResponse.model_validate(node)
            for node in await self._node_repository.get_all(session=session, **filters)
        ]

    async def get_node(self, session: AsyncSession, node_id: int) -> NodeResponse:
        """Fetch a node by ID."""
        node = await self._node_repository.get_by(session=session, id=node_id)
        if not node:
            resource = "Node"
            raise ResourceNotFoundError(resource)
        return NodeResponse.model_validate(node)

    async def update_node(
        self, session: AsyncSession, node_id: int, data: NodeUpdate
    ) -> NodeResponse:
        """Update a node by ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_node(session=session, node_id=node_id)

        node = await self._node_repository.update_by(
            session=session,
            data=update_data,
            id=node_id,
        )
        if not node:
            resource = "Node"
            raise ResourceNotFoundError(resource)
        return NodeResponse.model_validate(node)

    async def delete_node(self, session: AsyncSession, node_id: int) -> None:
        """Delete a node by ID."""
        deleted = await self._node_repository.delete_by(session=session, id=node_id)
        if not deleted:
            resource = "Node"
            raise ResourceNotFoundError(resource)
