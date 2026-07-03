"""Base contracts for execution node handlers."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

OnToken = Callable[[str], Awaitable[None]]


@dataclass(frozen=True)
class NodeExecutionContext:
    """Execution context passed to a node handler."""

    session: AsyncSession
    workflow_owner_id: int
    node_data: dict[str, object]
    parent_values: list[str]
    input_value: str
    on_token: OnToken | None = None


class NodeHandler(Protocol):
    """Protocol for node handlers."""

    async def execute(self, context: NodeExecutionContext) -> str:
        """Execute node logic and return node output."""
