"""Shared Redis client dependency."""

from fastapi import Request
from redis.asyncio import Redis


def get_redis_client(request: Request) -> Redis:
    """Return the shared Redis client stored on application state.

    Args:
        request: The incoming request.

    Returns:
        The shared Redis client.

    """
    return request.app.state.redis_client
