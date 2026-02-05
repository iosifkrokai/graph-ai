"""Repository for input nodes."""

from models import InputNode
from repositories.base import BaseRepository


class InputNodeRepository(BaseRepository[InputNode]):
    """Repository for InputNode model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the InputNode model."""
        super().__init__(model=InputNode)
