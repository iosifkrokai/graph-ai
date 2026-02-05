"""Custom exception types for the API."""

from exceptions.bad_request import BadRequestError
from exceptions.base import BaseError
from exceptions.conflict import ConflictError
from exceptions.not_found import ResourceNotFoundError

__all__ = [
    "BadRequestError",
    "BaseError",
    "ConflictError",
    "ResourceNotFoundError",
]
