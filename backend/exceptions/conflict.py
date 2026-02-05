"""Conflict exception."""

from http import HTTPStatus

from exceptions.base import BaseError


class ConflictError(BaseError):
    """Error raised when a resource conflicts with an existing state."""

    def __init__(self, message: str = "Conflict") -> None:
        """Create a conflict error with an optional message."""
        super().__init__(message=message, status_code=HTTPStatus.CONFLICT)
