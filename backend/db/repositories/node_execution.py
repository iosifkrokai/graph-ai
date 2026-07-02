"""Repository for node executions."""

from db.models import NodeExecution
from db.repositories.base import BaseRepository


class NodeExecutionRepository(BaseRepository[NodeExecution]):
    """Repository for NodeExecution model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the NodeExecution model."""
        super().__init__(model=NodeExecution)
