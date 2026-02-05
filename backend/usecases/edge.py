"""Usecase logic for edges."""

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import BadRequestError, ResourceNotFoundError
from repositories import EdgeRepository, NodeRepository, WorkflowRepository
from schemas import EdgeCreate, EdgeResponse, EdgeUpdate


class EdgeUsecase:
    """Usecase operations for edges."""

    def __init__(self) -> None:
        """Initialize repositories for edge operations."""
        self._edge_repository = EdgeRepository()
        self._node_repository = NodeRepository()
        self._workflow_repository = WorkflowRepository()

    async def create_edge(
        self, session: AsyncSession, data: EdgeCreate
    ) -> EdgeResponse:
        """Create an edge between nodes in a workflow."""
        workflow = await self._workflow_repository.get_by(
            session=session, id=data.workflow_id
        )
        if not workflow:
            resource = "Workflow"
            raise ResourceNotFoundError(resource)

        source_node = await self._node_repository.get_by(
            session=session, id=data.source_node_id
        )
        if not source_node:
            resource = "Source node"
            raise ResourceNotFoundError(resource)

        target_node = await self._node_repository.get_by(
            session=session, id=data.target_node_id
        )
        if not target_node:
            resource = "Target node"
            raise ResourceNotFoundError(resource)

        if source_node.workflow_id != data.workflow_id:
            message = "Source node does not belong to workflow"
            raise BadRequestError(message)
        if target_node.workflow_id != data.workflow_id:
            message = "Target node does not belong to workflow"
            raise BadRequestError(message)

        edge = await self._edge_repository.create(
            session=session,
            data={
                "workflow_id": data.workflow_id,
                "source_node_id": data.source_node_id,
                "target_node_id": data.target_node_id,
            },
        )
        return EdgeResponse.model_validate(edge)

    async def get_edges(
        self, session: AsyncSession, workflow_id: int | None = None
    ) -> list[EdgeResponse]:
        """List edges, optionally filtered by workflow."""
        filters = {"workflow_id": workflow_id} if workflow_id else {}
        return [
            EdgeResponse.model_validate(edge)
            for edge in await self._edge_repository.get_all(session=session, **filters)
        ]

    async def get_edge(self, session: AsyncSession, edge_id: int) -> EdgeResponse:
        """Fetch an edge by ID."""
        edge = await self._edge_repository.get_by(session=session, id=edge_id)
        if not edge:
            resource = "Edge"
            raise ResourceNotFoundError(resource)
        return EdgeResponse.model_validate(edge)

    async def update_edge(
        self, session: AsyncSession, edge_id: int, data: EdgeUpdate
    ) -> EdgeResponse:
        """Update an edge by ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_edge(session=session, edge_id=edge_id)

        edge = await self._edge_repository.update_by(
            session=session,
            data=update_data,
            id=edge_id,
        )
        if not edge:
            resource = "Edge"
            raise ResourceNotFoundError(resource)
        return EdgeResponse.model_validate(edge)

    async def delete_edge(self, session: AsyncSession, edge_id: int) -> None:
        """Delete an edge by ID."""
        deleted = await self._edge_repository.delete_by(session=session, id=edge_id)
        if not deleted:
            resource = "Edge"
            raise ResourceNotFoundError(resource)
