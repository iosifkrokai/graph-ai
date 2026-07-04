"""Telegram bot dependency providers."""

from usecases import TelegramBotUsecase


def get_telegram_bot_usecase() -> TelegramBotUsecase:
    """Get the Telegram bot usecase.

    Returns:
        The Telegram bot usecase.

    """
    return TelegramBotUsecase()
