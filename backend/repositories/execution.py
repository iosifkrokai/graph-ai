"""Repository for executions."""

from models import Execution
from repositories.base import BaseRepository


class ExecutionRepository(BaseRepository[Execution]):
    """Repository for Execution model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the Execution model."""
        super().__init__(model=Execution)
