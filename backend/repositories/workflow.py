"""Repository for workflows."""

from models import Workflow
from repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for Workflow model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the Workflow model."""
        super().__init__(model=Workflow)
