"""Settings for the RAG (vector store + embeddings) subsystem."""

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from settings.base import BaseSettings


class RagSettings(BaseSettings):
    """Configuration for Qdrant connectivity and the local embedding model."""

    model_config = SettingsConfigDict(env_prefix="rag_")

    qdrant_host: str = Field(default="qdrant", title="Qdrant host")
    qdrant_port: int = Field(default=6333, title="Qdrant port")
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        title="fastembed model name",
    )
    embedding_cache_dir: str = Field(
        default="/tmp/fastembed_cache",  # noqa: S108
        title="Directory fastembed caches downloaded model files in",
    )


rag_settings = RagSettings()
