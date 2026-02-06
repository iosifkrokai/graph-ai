"""Node use case implementation."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import NodeNotFoundError, WorkflowNotFoundError
from models import Node, Workflow
from repositories import NodeRepository, WorkflowRepository


class NodeUsecase:
    """Node business logic."""

    def __init__(self) -> None:
        """Initialize the usecase."""
        self._node_repository = NodeRepository()
        self._workflow_repository = WorkflowRepository()

    async def create_node(
        self,
        session: AsyncSession,
        user_id: int,
        **kwargs: object,
    ) -> Node:
        """Create a node within a workflow.

        Args:
            session: The session.
            user_id: The owner user ID.
            **kwargs: The node creation fields.

        Returns:
            The created node.

        Raises:
            WorkflowNotFoundError: If the workflow is not found.

        """
        workflow = await self._workflow_repository.get_by(
            session=session, id=kwargs["workflow_id"], owner_id=user_id
        )
        if not workflow:
            raise WorkflowNotFoundError

        return await self._node_repository.create(
            session=session,
            data=kwargs,
        )

    async def get_nodes(
        self, session: AsyncSession, user_id: int, workflow_id: int | None = None
    ) -> list[Node]:
        """List nodes, optionally filtered by workflow.

        Args:
            session: The session.
            user_id: The owner user ID.
            workflow_id: The workflow ID.

        Returns:
            The list of nodes.

        """
        if workflow_id is not None:
            workflow = await self._workflow_repository.get_by(
                session=session, id=workflow_id, owner_id=user_id
            )
            if not workflow:
                raise WorkflowNotFoundError

        statement = (
            select(Node)
            .join(Workflow, Node.workflow_id == Workflow.id)
            .where(Workflow.owner_id == user_id)
            .order_by(Node.id.asc())
        )
        if workflow_id is not None:
            statement = statement.where(Node.workflow_id == workflow_id)

        result = await session.execute(statement=statement)
        return list(result.scalars().all())

    async def get_node(self, session: AsyncSession, node_id: int, user_id: int) -> Node:
        """Fetch a node by ID.

        Args:
            session: The session.
            node_id: The node ID.
            user_id: The owner user ID.

        Returns:
            The node.

        Raises:
            NodeNotFoundError: If the node is not found.

        """
        result = await session.execute(
            statement=select(Node)
            .join(Workflow, Node.workflow_id == Workflow.id)
            .where(Node.id == node_id, Workflow.owner_id == user_id)
        )
        node = result.scalar_one_or_none()
        if not node:
            raise NodeNotFoundError
        return node

    async def update_node(
        self, session: AsyncSession, node_id: int, user_id: int, **kwargs: object
    ) -> Node:
        """Update a node by ID.

        Args:
            session: The session.
            node_id: The node ID.
            user_id: The owner user ID.
            **kwargs: The fields to update.

        Returns:
            The updated node.

        Raises:
            NodeNotFoundError: If the node is not found.

        """
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        if not update_data:
            return await self.get_node(
                session=session, node_id=node_id, user_id=user_id
            )

        await self.get_node(session=session, node_id=node_id, user_id=user_id)
        node = await self._node_repository.update_by(
            session=session,
            data=update_data,
            id=node_id,
        )
        if not node:
            raise NodeNotFoundError
        return node

    async def delete_node(
        self, session: AsyncSession, node_id: int, user_id: int
    ) -> None:
        """Delete a node by ID.

        Args:
            session: The session.
            node_id: The node ID.
            user_id: The owner user ID.

        Raises:
            NodeNotFoundError: If the node is not found.

        """
        await self.get_node(session=session, node_id=node_id, user_id=user_id)
        deleted = await self._node_repository.delete_by(session=session, id=node_id)
        if not deleted:
            raise NodeNotFoundError
