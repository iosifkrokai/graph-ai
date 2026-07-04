"""Repository for Telegram bots."""

from db.models import TelegramBot
from db.repositories.base import BaseRepository


class TelegramBotRepository(BaseRepository[TelegramBot]):
    """Repository for TelegramBot model operations."""

    def __init__(self) -> None:
        """Initialize the repository with the TelegramBot model."""
        super().__init__(model=TelegramBot)
