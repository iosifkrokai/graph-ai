"""Redis pub/sub for streaming per-node LLM tokens to clients."""

import json
from collections.abc import AsyncIterator

from redis.asyncio import Redis


def token_channel(execution_id: int) -> str:
    """Return the pub/sub channel name for an execution's token stream.

    Args:
        execution_id: The execution ID.

    Returns:
        The Redis channel name.

    """
    return f"execution:{execution_id}:tokens"


async def publish_token(
    redis: Redis,
    execution_id: int,
    node_id: int,
    delta: str,
) -> None:
    """Publish one token delta for a node to the execution's channel.

    Args:
        redis: Redis connection.
        execution_id: The execution ID.
        node_id: The node emitting the delta.
        delta: The token text.

    """
    message = json.dumps({"node_id": node_id, "delta": delta})
    await redis.publish(token_channel(execution_id), message)


async def subscribe_tokens(
    redis: Redis,
    execution_id: int,
) -> AsyncIterator[tuple[int, str]]:
    """Yield ``(node_id, delta)`` pairs published for an execution.

    Args:
        redis: Redis connection.
        execution_id: The execution ID.

    Yields:
        Node ID and token delta for each published message.

    """
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(token_channel(execution_id))
    try:
        async for message in pubsub.listen():
            raw = message["data"]
            data = raw.decode() if isinstance(raw, bytes) else raw
            payload = json.loads(data)
            yield int(payload["node_id"]), str(payload["delta"])
    finally:
        await pubsub.unsubscribe(token_channel(execution_id))
        await pubsub.aclose()
