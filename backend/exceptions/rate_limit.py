"""Rate-limit exceptions."""

from http import HTTPStatus

from exceptions.base import BaseError


class RateLimitExceededError(BaseError):
    """Raised when a client exceeds a rate limit."""

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        status_code: HTTPStatus = HTTPStatus.TOO_MANY_REQUESTS,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)
