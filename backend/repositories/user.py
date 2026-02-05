"""Repository for users."""

from models import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the User model."""
        super().__init__(model=User)
