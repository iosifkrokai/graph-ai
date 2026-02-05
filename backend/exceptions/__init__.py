"""Custom exception types for the API."""

from exceptions.auth import AuthCredentialsError
from exceptions.bad_request import BadRequestError
from exceptions.base import BaseError
from exceptions.conflict import ConflictError
from exceptions.not_found import ResourceNotFoundError
from exceptions.user import UserAlreadyExistsError, UserNotFoundError

__all__ = [
    "AuthCredentialsError",
    "BadRequestError",
    "BaseError",
    "ConflictError",
    "ResourceNotFoundError",
    "UserAlreadyExistsError",
    "UserNotFoundError",
]
