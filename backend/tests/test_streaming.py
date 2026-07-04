"""Token streaming: node token sink and Redis pub/sub round-trip."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
import pytest_asyncio
from redis.asyncio import Redis
from testcontainers.redis import RedisContainer

from enums import LLMProviderType
from nodes import llm as llm_module
from nodes.base import NodeExecutionContext
from streaming import publish_token, subscribe_tokens, token_channel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from db.repositories import LLMProviderRepository

_EXECUTION_ID = 42
_NODE_ID = 7
_DELTAS = ["Hello", ", ", "world"]


class _StubStreamingClient:
    """LLM client stub that streams a fixed sequence of deltas."""

    def __init__(self, deltas: list[str]) -> None:
        """Store the deltas to emit."""
        self._deltas = deltas

    async def stream_chat(self, *args: object, **kwargs: object) -> AsyncIterator[str]:
        """Yield the configured deltas."""
        del args, kwargs
        for delta in self._deltas:
            yield delta


class _StubProviderRepository:
    """Repository stub returning a fixed Ollama provider row."""

    async def get_by(self, *args: object, **kwargs: object) -> SimpleNamespace:
        """Return a minimal Ollama provider row without an API key."""
        del args, kwargs
        return SimpleNamespace(
            id=1,
            user_id=1,
            name="p",
            type=LLMProviderType.OLLAMA,
            base_url="http://ollama:11434",
            config={},
            api_key=None,
        )


class TestNodeTokenSink:
    """Tests for the LLM node streaming path via on_token."""

    @pytest.mark.asyncio
    async def test_streams_and_accumulates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The node forwards each delta and returns the concatenation."""
        monkeypatch.setattr(
            llm_module,
            "create_llm_client",
            lambda **_: _StubStreamingClient(_DELTAS),
        )

        collected: list[str] = []

        async def on_token(delta: str) -> None:
            """Record each streamed delta."""
            collected.append(delta)

        handler = llm_module.LLMNodeHandler(
            llm_provider_repository=cast(
                "LLMProviderRepository", _StubProviderRepository()
            )
        )
        result = await handler.execute(
            NodeExecutionContext(
                session=cast("AsyncSession", None),
                workflow_owner_id=1,
                node_data={"llm_provider_id": 1, "model": "m", "system_prompt": ""},
                parent_values=["prompt"],
                input_value="prompt",
                on_token=on_token,
            )
        )

        if collected != _DELTAS:
            pytest.fail("Each delta should have been forwarded to on_token")
        if result.output != "".join(_DELTAS):
            pytest.fail("Node output should be the concatenated deltas")


class TestTokenPubSub:
    """Tests for the Redis token pub/sub round-trip."""

    @pytest_asyncio.fixture
    async def redis(self) -> AsyncGenerator[Redis, None]:
        """Spin up a throwaway Redis and yield an async client."""
        with RedisContainer() as container:
            client: Redis = Redis(
                host=container.get_container_host_ip(),
                port=int(container.get_exposed_port(6379)),
            )
            try:
                yield client
            finally:
                await client.aclose()

    def test_channel_name(self) -> None:
        """The channel name is namespaced by execution ID."""
        if token_channel(_EXECUTION_ID) != f"execution:{_EXECUTION_ID}:tokens":
            pytest.fail("Unexpected channel name")

    @pytest.mark.asyncio
    async def test_publish_then_subscribe_round_trip(self, redis: Redis) -> None:
        """Published deltas are received in order by a subscriber."""
        deltas = ["a", "b", "c"]
        received: list[tuple[int, str]] = []
        ready = asyncio.Event()

        async def consume() -> None:
            """Collect published deltas until all arrive."""
            async for node_id, delta in subscribe_tokens(redis, _EXECUTION_ID):
                received.append((node_id, delta))
                if len(received) == len(deltas):
                    return

        async def produce() -> None:
            """Publish deltas once the subscription is active."""
            await ready.wait()
            for delta in deltas:
                await publish_token(redis, _EXECUTION_ID, _NODE_ID, delta)

        consumer = asyncio.create_task(consume())
        # Give the subscriber a moment to subscribe before publishing.
        await asyncio.sleep(0.2)
        ready.set()
        await produce()
        await asyncio.wait_for(consumer, timeout=5)

        if received != [(_NODE_ID, delta) for delta in deltas]:
            pytest.fail("Subscriber did not receive published deltas in order")
