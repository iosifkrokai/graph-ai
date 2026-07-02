"""Redis settings."""

from arq.connections import RedisSettings as ArqRedisSettings
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from settings.base import BaseSettings


class RedisSettings(BaseSettings):
    """Configuration for Redis / ARQ connections."""

    model_config = SettingsConfigDict(env_prefix="redis_")

    host: str = Field(default="redis", title="Redis host")
    port: int = Field(default=6379, title="Redis port")
    db: int = Field(default=0, title="Redis database")

    @property
    def arq(self) -> ArqRedisSettings:
        """Build ARQ RedisSettings from configuration.

        Returns:
            ARQ connection settings.

        """
        return ArqRedisSettings(host=self.host, port=self.port, database=self.db)


redis_settings = RedisSettings()
