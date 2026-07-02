"""Queue (ARQ) dependency providers."""

from arq import ArqRedis
from fastapi import Request


def get_arq_pool(request: Request) -> ArqRedis:
    """Return the ARQ pool stored on application state.

    Args:
        request: The incoming request.

    Returns:
        The ARQ Redis pool.

    """
    return request.app.state.arq_pool
