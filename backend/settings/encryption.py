"""Encryption settings."""

from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict

from settings.base import BaseSettings

PRODUCTION_ENVIRONMENT = "production"


class EncryptionSettings(BaseSettings):
    """Configuration for symmetric secret encryption (Fernet)."""

    model_config = SettingsConfigDict(env_prefix="encryption_")

    environment: str = Field(
        default="local",
        title="Environment",
        validation_alias="ENVIRONMENT",
    )
    # Insecure development key; must be overridden in production via
    # ENCRYPTION_SECRET_KEY (a urlsafe base64-encoded 32-byte Fernet key).
    secret_key: str = Field(
        default="ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
        title="Fernet secret key",
    )

    @model_validator(mode="after")
    def _reject_default_key_in_production(self) -> Self:
        """Fail fast when the encryption key is left at its default in production.

        Returns:
            The validated settings instance.

        Raises:
            ValueError: If running in production without overriding the key.

        """
        default_key = type(self).model_fields["secret_key"].default
        if (
            self.environment.lower() == PRODUCTION_ENVIRONMENT
            and self.secret_key == default_key
        ):
            message = (
                "ENCRYPTION_SECRET_KEY must be set to a non-default value when "
                "ENVIRONMENT=production"
            )
            raise ValueError(message)

        return self


encryption_settings = EncryptionSettings()
