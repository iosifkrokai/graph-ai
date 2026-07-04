"""Qdrant access helpers shared by the Vector Ingest/Search node handlers."""

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams

from settings import rag_settings

_CHUNK_SIZE = 800
_CHUNK_OVERLAP = 100


def get_qdrant_client() -> AsyncQdrantClient:
    """Build a fresh Qdrant client from global settings."""
    return AsyncQdrantClient(
        host=rag_settings.qdrant_host, port=rag_settings.qdrant_port
    )


def chunk_text(
    text: str, size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP
) -> list[str]:
    """Split text into fixed-size, overlapping character chunks."""
    stripped = text.strip()
    if not stripped:
        return []
    chunks: list[str] = []
    step = size - overlap
    for start in range(0, len(stripped), step):
        chunk = stripped[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
        if start + size >= len(stripped):
            break
    return chunks


async def ensure_collection(
    client: AsyncQdrantClient, name: str, vector_size: int
) -> None:
    """Create the collection with the given vector size if it doesn't exist yet."""
    if not await client.collection_exists(name):
        await client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
