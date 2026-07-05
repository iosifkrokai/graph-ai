"""User-related exceptions."""

from http import HTTPStatus

from exceptions.base import BaseError


class UserNotFoundError(BaseError):
    """Raised when a user cannot be found."""

    def __init__(
        self,
        message: str = "User not found",
        status_code: HTTPStatus = HTTPStatus.NOT_FOUND,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)


class UserAlreadyExistsError(BaseError):
    """Raised when a user already exists.

    The message is deliberately generic — it must not confirm that the
    email is already registered, the same way a failed login never
    confirms whether the email exists.
    """

    def __init__(
        self,
        message: str = "Unable to register with the provided details",
        status_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)
