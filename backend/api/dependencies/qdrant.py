"""Qdrant client dependency."""

from collections.abc import AsyncGenerator

from qdrant_client import AsyncQdrantClient

from rag.qdrant import get_qdrant_client as build_qdrant_client


async def get_qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    """Yield a fresh Qdrant client, closed after the request.

    Yields:
        A Qdrant client.

    """
    client = build_qdrant_client()
    try:
        yield client
    finally:
        await client.close()
