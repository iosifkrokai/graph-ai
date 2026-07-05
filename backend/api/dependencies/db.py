"""Database dependency providers."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sessions import async_session


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get the session.

    Yields:
        The session.

    """
    async with async_session() as session:
        yield session


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory.

    For callers that need to open their own short-lived session (e.g. a
    health check) rather than one scoped to the request.

    Returns:
        The session factory.

    """
    return async_session
