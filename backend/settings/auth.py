"""Authentication settings."""

from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from settings.base import BaseSettings

PRODUCTION_ENVIRONMENT = "production"


class AuthSettings(BaseSettings):
    """Auth configuration loaded from environment."""

    model_config = SettingsConfigDict(env_prefix="auth_")

    environment: str = Field(
        default="local",
        title="Environment",
        validation_alias="ENVIRONMENT",
    )
    secret_key: str = Field(default="secret", title="Secret key")
    algorithm: str = Field(default="HS256", title="Algorithm")
    access_token_expire_minutes: int = Field(
        default=30, title="Access token expire minutes"
    )
    token_type: str = Field(default="Bearer", title="Token type")

    @model_validator(mode="after")
    def _reject_default_secret_in_production(self) -> Self:
        """Fail fast when the secret key is left at its default in production.

        Returns:
            The validated settings instance.

        Raises:
            ValueError: If running in production without overriding the secret key.

        """
        default_secret = type(self).model_fields["secret_key"].default
        if (
            self.environment.lower() == PRODUCTION_ENVIRONMENT
            and self.secret_key == default_secret
        ):
            message = (
                "AUTH_SECRET_KEY must be set to a non-default value when "
                "ENVIRONMENT=production"
            )
            raise ValueError(message)

        return self


auth_settings = AuthSettings()
