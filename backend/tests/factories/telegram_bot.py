"""Telegram bot model factory."""

from factory.declarations import LazyAttribute

from db.models import TelegramBot
from tests.factories.base import AsyncSQLAlchemyModelFactory, fake
from utils.encryption import encrypt


class TelegramBotFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating TelegramBot instances."""

    class Meta:
        """Factory meta configuration."""

        model = TelegramBot

    user_id = None
    name = LazyAttribute(lambda _obj: f"bot-{fake.word()}")
    bot_token = LazyAttribute(lambda _obj: encrypt(fake.uuid4()))
    last_update_id = 0
    enabled = True
