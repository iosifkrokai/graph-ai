"""Repository for output nodes."""

from models import OutputNode
from repositories.base import BaseRepository


class OutputNodeRepository(BaseRepository[OutputNode]):
    """Repository for OutputNode model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the OutputNode model."""
        super().__init__(model=OutputNode)
