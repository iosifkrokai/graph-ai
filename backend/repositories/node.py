"""Repository for nodes."""

from models import Node
from repositories.base import BaseRepository


class NodeRepository(BaseRepository[Node]):
    """Repository for Node model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the Node model."""
        super().__init__(model=Node)
