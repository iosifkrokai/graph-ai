"""CORS settings."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from settings.base import BaseSettings


class CorsSettings(BaseSettings):
    """Configuration for the CORS allowed-origin allowlist."""

    model_config = SettingsConfigDict(env_prefix="cors_")

    allowed_origins: str = Field(
        default="http://localhost:3000",
        title="Comma-separated list of allowed CORS origins",
    )

    @property
    def origins(self) -> list[str]:
        """Return the allowed origins as a list."""
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


cors_settings = CorsSettings()
