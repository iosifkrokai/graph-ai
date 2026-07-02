"""Pytest fixtures for backend tests."""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from api.dependencies import db, queue
from db.models import Base
from main import app
from settings import postgres_settings


class _NoopArqPool:
    """Stand-in ARQ pool that drops enqueued jobs during tests."""

    async def enqueue_job(self, *args: object, **kwargs: object) -> None:
        """Accept and ignore an enqueue call."""
        del args, kwargs


@pytest_asyncio.fixture(scope="session")
async def postgres_container() -> AsyncGenerator[PostgresContainer, None]:
    """Spin up a Postgres container for the test session."""
    with PostgresContainer(image=postgres_settings.image, driver="asyncpg") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="function")
async def test_engine(
    postgres_container: PostgresContainer,
) -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh database engine for each test."""
    engine = create_async_engine(
        url=postgres_container.get_connection_url(),
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for tests."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def test_client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client with the test session injected."""

    def override_get_session() -> AsyncSession:
        """Return the test session for dependency overrides."""
        return test_session

    def override_get_arq_pool() -> _NoopArqPool:
        """Return a no-op ARQ pool so tests need no Redis."""
        return _NoopArqPool()

    app.dependency_overrides[db.get_session] = override_get_session
    app.dependency_overrides[queue.get_arq_pool] = override_get_arq_pool

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
