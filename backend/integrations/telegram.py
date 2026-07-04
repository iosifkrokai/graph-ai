"""Thin client for the Telegram Bot API."""

from typing import Any

import httpx

from constants.timeout import DEFAULT_TIMEOUT
from exceptions import TelegramAPIError

_BASE_URL = "https://api.telegram.org"


def _api_url(bot_token: str, method: str) -> str:
    """Build the Telegram Bot API URL for a method call."""
    return f"{_BASE_URL}/bot{bot_token}/{method}"


async def _call(
    bot_token: str, method: str, payload: dict[str, Any]
) -> dict[str, Any] | list[Any] | None:
    """POST to a Telegram Bot API method and return its ``result`` field.

    Args:
        bot_token: The bot token.
        method: The Bot API method name (e.g. ``getUpdates``).
        payload: The JSON request body.

    Returns:
        The decoded ``result`` field of the response.

    Raises:
        TelegramAPIError: If the request fails or Telegram reports an error.

    """
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(_api_url(bot_token, method), json=payload)
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        message = f"Telegram {method} timed out"
        raise TelegramAPIError(message=message) from exc
    except httpx.HTTPStatusError as exc:
        message = f"Telegram {method} returned {exc.response.status_code}"
        raise TelegramAPIError(message=message) from exc
    except httpx.HTTPError as exc:
        raise TelegramAPIError from exc

    body = response.json()
    if not body.get("ok"):
        message = f"Telegram {method} failed: {body.get('description')}"
        raise TelegramAPIError(message=message)

    return body.get("result")


async def get_updates(
    bot_token: str, offset: int, poll_seconds: int = 0
) -> list[dict[str, Any]]:
    """Fetch new updates for a bot since ``offset``.

    Args:
        bot_token: The bot token.
        offset: The lowest update_id to return (typically ``last_update_id + 1``).
        poll_seconds: Long-poll duration in seconds; 0 for a short poll.

    Returns:
        The list of raw Telegram update objects.

    Raises:
        TelegramAPIError: If the request fails.

    """
    result = await _call(
        bot_token, "getUpdates", {"offset": offset, "timeout": poll_seconds}
    )
    return result if isinstance(result, list) else []


async def send_message(bot_token: str, chat_id: int, text: str) -> None:
    """Send a text message to a chat.

    Args:
        bot_token: The bot token.
        chat_id: The destination chat ID.
        text: The message text.

    Raises:
        TelegramAPIError: If the request fails.

    """
    await _call(bot_token, "sendMessage", {"chat_id": chat_id, "text": text})
