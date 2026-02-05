"""Bad request exception."""

from http import HTTPStatus

from exceptions.base import BaseError


class BadRequestError(BaseError):
    """Error raised when a request is invalid."""

    def __init__(self, message: str = "Bad request") -> None:
        """Create a bad request error with an optional message."""
        super().__init__(message=message, status_code=HTTPStatus.BAD_REQUEST)
