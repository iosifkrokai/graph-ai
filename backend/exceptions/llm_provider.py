"""LLM provider-related exceptions."""

from http import HTTPStatus

from exceptions.base import BaseError


class LLMProviderNotFoundError(BaseError):
    """Raised when an LLM provider cannot be found."""

    def __init__(
        self,
        message: str = "LLM provider not found",
        status_code: HTTPStatus = HTTPStatus.NOT_FOUND,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)


class LLMProviderConnectionError(BaseError):
    """Raised when the LLM provider is unreachable."""

    retryable = True

    def __init__(
        self,
        message: str = "LLM provider is unreachable",
        status_code: HTTPStatus = HTTPStatus.BAD_GATEWAY,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)


class LLMProviderConfigError(BaseError):
    """Raised when the LLM provider configuration is invalid."""

    def __init__(
        self,
        message: str = "LLM provider configuration is invalid",
        status_code: HTTPStatus = HTTPStatus.CONFLICT,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)


class UnsupportedLLMProviderError(BaseError):
    """Raised when the LLM provider type is unsupported."""

    def __init__(
        self,
        message: str = "LLM provider type is not supported",
        status_code: HTTPStatus = HTTPStatus.NOT_IMPLEMENTED,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)


class LLMProviderAlreadyExistsError(BaseError):
    """Raised when a provider with the same name already exists for this user."""

    def __init__(
        self,
        message: str = "A provider with this name already exists",
        status_code: HTTPStatus = HTTPStatus.CONFLICT,
    ) -> None:
        """Initialize the error."""
        super().__init__(message=message, status_code=status_code)
