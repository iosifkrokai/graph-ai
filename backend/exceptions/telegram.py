"""Telegram-related exceptions."""

from http import HTTPStatus

from exceptions.base import BaseError


class TelegramBotNotFoundError(BaseError):
    """Raised when a Telegram bot cannot be found."""

    def __init__(
        self,
        message: str = "Telegram bot not found",
        status_code: HTTPStatus = HTTPStatus.NOT_FOUND,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)


class TelegramAPIError(BaseError):
    """Raised when a call to the Telegram Bot API fails."""

    retryable = True

    def __init__(
        self,
        message: str = "Telegram API request failed",
        status_code: HTTPStatus = HTTPStatus.BAD_GATEWAY,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)
