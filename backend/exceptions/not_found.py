"""Not found exception."""

from http import HTTPStatus

from exceptions.base import BaseError


class ResourceNotFoundError(BaseError):
    """Error raised when a requested resource does not exist."""

    def __init__(self, resource: str, message: str | None = None) -> None:
        """Create a not-found error for a resource."""
        super().__init__(
            message=message or f"{resource} not found",
            status_code=HTTPStatus.NOT_FOUND,
        )
        self.resource = resource
