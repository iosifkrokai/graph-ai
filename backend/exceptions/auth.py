"""Auth-related exceptions."""

from http import HTTPStatus

from exceptions.base import BaseError


class AuthCredentialsError(BaseError):
    """Raised when auth credentials are invalid."""

    def __init__(
        self,
        message: str = "Could not validate credentials",
        status_code: HTTPStatus = HTTPStatus.UNAUTHORIZED,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)
