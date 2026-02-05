"""Repository for LLM nodes."""

from models import LLMNode
from repositories.base import BaseRepository


class LLMNodeRepository(BaseRepository[LLMNode]):
    """Repository for LLMNode model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the LLMNode model."""
        super().__init__(model=LLMNode)
