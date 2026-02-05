"""Base exception types for the API layer."""

from http import HTTPStatus


class BaseError(Exception):
    """Base exception carrying an HTTP status code and message."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR,
    ) -> None:
        """Initialize the error with a message and HTTP status code."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
