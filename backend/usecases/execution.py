"""Execution use case implementation."""

import asyncio
import logging
from collections import deque
from collections.abc import AsyncGenerator, Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from constants import (
    MAX_NODE_ATTEMPTS,
    NODE_TIMEOUT_SECONDS,
    RETRY_BACKOFF_BASE_SECONDS,
    STREAM_MAX_ITERATIONS,
    STREAM_POLL_SECONDS,
    STUCK_EXECUTION_TIMEOUT_SECONDS,
)
from db.repositories import (
    EdgeRepository,
    ExecutionRepository,
    LLMProviderRepository,
    NodeExecutionRepository,
    NodeRepository,
    WorkflowRepository,
)
from enums import ExecutionStatus, NodeType
from exceptions import (
    BaseError,
    ExecutionGraphValidationError,
    ExecutionInputValidationError,
    ExecutionNotFoundError,
    NodeExecutionTimeoutError,
    WorkflowNotFoundError,
)
from nodes import NodeExecutionContext, NodeHandlerRegistry
from schemas import (
    EdgeResponse,
    ExecutionCreate,
    ExecutionGraphContext,
    ExecutionOutputPayload,
    ExecutionResponse,
    NodeExecutionResponse,
    NodeResponse,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _NodeRunContext:
    """Loop-invariant context shared across node executions in one run."""

    execution_id: int
    workflow_owner_id: int
    input_value: str


@dataclass(frozen=True)
class _NodeOutcome:
    """Final result of a single node execution."""

    status: ExecutionStatus
    output: str | None = None
    error: str | None = None


class ExecutionUsecase:
    """Execution business logic."""

    _max_node_attempts: int = MAX_NODE_ATTEMPTS
    _node_timeout_seconds: float = NODE_TIMEOUT_SECONDS

    def __init__(self) -> None:
        """Initialize the usecase."""
        self._execution_repository = ExecutionRepository()
        self._workflow_repository = WorkflowRepository()
        self._node_repository = NodeRepository()
        self._edge_repository = EdgeRepository()
        self._node_execution_repository = NodeExecutionRepository()
        self._llm_provider_repository = LLMProviderRepository()
        self._node_registry = NodeHandlerRegistry(
            llm_provider_repository=self._llm_provider_repository
        )

    async def create_execution(
        self,
        session: AsyncSession,
        user_id: int,
        data: ExecutionCreate,
        enqueue: Callable[[int], Awaitable[None]],
    ) -> ExecutionResponse:
        """Validate a workflow, persist a queued execution, and enqueue it.

        The graph is validated synchronously so invalid workflows fail fast with a
        4xx before any background work is scheduled. The actual run happens on a
        worker via ``run_execution``.

        Args:
            session: The session.
            user_id: The owner user ID.
            data: The execution payload.
            enqueue: Callback that schedules the execution for background running.

        Returns:
            The created execution in ``CREATED`` (queued) state.

        Raises:
            WorkflowNotFoundError: If the workflow is not found.
            ExecutionGraphValidationError: If graph is invalid for execution.

        """
        workflow = await self._workflow_repository.get_by(
            session=session,
            id=data.workflow_id,
            owner_id=user_id,
        )
        if not workflow:
            raise WorkflowNotFoundError

        # Validate the graph up front (fail-fast); the worker rebuilds it at run time.
        await self._load_graph(session=session, workflow_id=data.workflow_id)

        execution = await self._execution_repository.create(
            session=session,
            data={
                "workflow_id": data.workflow_id,
                "input_data": data.input_data.model_dump(),
                "status": ExecutionStatus.CREATED,
            },
        )

        await enqueue(execution.id)

        return await self.get_execution(
            session=session, execution_id=execution.id, user_id=user_id
        )

    async def run_execution(
        self,
        session: AsyncSession,
        execution_id: int,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> ExecutionResponse:
        """Run a queued execution to completion (worker entry point).

        Args:
            session: The session (owned by the worker, not the request).
            execution_id: The execution to run.
            session_factory: When provided, independent graph branches run
                concurrently, each node on its own session. When ``None``, nodes
                run serially on ``session``.

        Returns:
            The finalized execution.

        Raises:
            ExecutionNotFoundError: If the execution is not found.
            WorkflowNotFoundError: If the workflow is not found.
            ExecutionGraphValidationError: If graph is invalid for execution.

        """
        execution = await self._execution_repository.get_by(
            session=session, id=execution_id
        )
        if execution is None:
            raise ExecutionNotFoundError

        workflow = await self._workflow_repository.get_by(
            session=session, id=execution.workflow_id
        )
        if workflow is None:
            raise WorkflowNotFoundError

        await self._execution_repository.update_by(
            session=session,
            id=execution_id,
            data={"status": ExecutionStatus.RUNNING},
        )

        graph = await self._load_graph(
            session=session, workflow_id=execution.workflow_id
        )

        try:
            output_data = await self._run_execution(
                session=session,
                execution_id=execution_id,
                graph=graph,
                session_factory=session_factory,
            )
        except BaseError as exc:
            logger.warning("Execution %s failed: %s", execution_id, exc.message)
            await self._mark_execution_failed(
                session=session, execution_id=execution_id, error=exc.message
            )
        except Exception:
            logger.exception("Execution %s failed with unexpected error", execution_id)
            await session.rollback()
            await self._mark_execution_failed(
                session=session,
                execution_id=execution_id,
                error="Internal execution error",
            )
        else:
            await self._mark_execution_success(
                session=session, execution_id=execution_id, output_data=output_data
            )

        finalized = await self._execution_repository.get_by(
            session=session, id=execution_id
        )
        if finalized is None:
            raise ExecutionNotFoundError

        return ExecutionResponse.model_validate(finalized)

    async def reap_stuck_executions(
        self,
        session: AsyncSession,
        older_than_seconds: int = STUCK_EXECUTION_TIMEOUT_SECONDS,
    ) -> int:
        """Mark executions stuck in RUNNING beyond the timeout as FAILED.

        Args:
            session: The session.
            older_than_seconds: Minimum age (by ``started_at``) to consider stuck.

        Returns:
            The number of executions reaped.

        """
        cutoff = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(
            seconds=older_than_seconds
        )
        running = await self._execution_repository.get_all(
            session=session, status=ExecutionStatus.RUNNING
        )
        stuck = [execution for execution in running if execution.started_at < cutoff]
        for execution in stuck:
            logger.warning("Reaping stuck execution %s", execution.id)
            await self._mark_execution_failed(
                session=session,
                execution_id=execution.id,
                error="Execution timed out (worker did not finish)",
            )

        return len(stuck)

    async def _load_graph(
        self, session: AsyncSession, workflow_id: int
    ) -> ExecutionGraphContext:
        """Build and validate the execution graph for a workflow.

        Args:
            session: The session.
            workflow_id: The workflow ID.

        Returns:
            The validated graph context.

        Raises:
            ExecutionGraphValidationError: If graph is invalid for execution.

        """
        return self._build_graph_context(
            nodes=[
                NodeResponse.model_validate(node)
                for node in await self._node_repository.get_all(
                    session=session, workflow_id=workflow_id
                )
            ],
            edges=[
                EdgeResponse.model_validate(edge)
                for edge in await self._edge_repository.get_all(
                    session=session, workflow_id=workflow_id
                )
            ],
        )

    async def get_executions(
        self, session: AsyncSession, user_id: int, workflow_id: int
    ) -> list[ExecutionResponse]:
        """List executions for a workflow.

        Args:
            session: The session.
            user_id: The owner user ID.
            workflow_id: The workflow ID.

        Returns:
            The list of executions.

        Raises:
            WorkflowNotFoundError: If the workflow is not found.

        """
        workflow = await self._workflow_repository.get_by(
            session=session, id=workflow_id, owner_id=user_id
        )
        if not workflow:
            raise WorkflowNotFoundError

        return [
            ExecutionResponse.model_validate(execution)
            for execution in await self._execution_repository.get_all(
                session=session, workflow_id=workflow_id
            )
        ]

    async def get_execution(
        self, session: AsyncSession, execution_id: int, user_id: int
    ) -> ExecutionResponse:
        """Fetch an execution by ID.

        Args:
            session: The session.
            execution_id: The execution ID.
            user_id: The owner user ID.

        Returns:
            The execution.

        Raises:
            ExecutionNotFoundError: If the execution is not found.
            WorkflowNotFoundError: If the workflow is not found.

        """
        execution = await self._execution_repository.get_by(
            session=session, id=execution_id
        )
        if not execution:
            raise ExecutionNotFoundError

        workflow = await self._workflow_repository.get_by(
            session=session, id=execution.workflow_id, owner_id=user_id
        )
        if not workflow:
            raise WorkflowNotFoundError

        return ExecutionResponse.model_validate(execution)

    async def get_node_executions(
        self, session: AsyncSession, execution_id: int, user_id: int
    ) -> list[NodeExecutionResponse]:
        """List per-node results for an execution.

        Args:
            session: The session.
            execution_id: The execution ID.
            user_id: The owner user ID.

        Returns:
            The list of node execution results.

        Raises:
            ExecutionNotFoundError: If the execution is not found.
            WorkflowNotFoundError: If the workflow is not owned by the user.

        """
        await self.get_execution(
            session=session, execution_id=execution_id, user_id=user_id
        )

        return [
            NodeExecutionResponse.model_validate(node_execution)
            for node_execution in await self._node_execution_repository.get_all(
                session=session, execution_id=execution_id
            )
        ]

    async def stream_execution(
        self, session: AsyncSession, execution_id: int, user_id: int
    ) -> AsyncGenerator[str, None]:
        """Yield SSE ``data:`` frames of an execution's status until terminal.

        Args:
            session: The session.
            execution_id: The execution ID.
            user_id: The owner user ID.

        Yields:
            SSE-formatted status frames, ending once the execution is terminal.

        """
        terminal = {ExecutionStatus.SUCCESS, ExecutionStatus.FAILED}
        for _ in range(STREAM_MAX_ITERATIONS):
            session.expire_all()
            execution = await self.get_execution(
                session=session, execution_id=execution_id, user_id=user_id
            )
            yield f"data: {execution.model_dump_json()}\n\n"
            if execution.status in terminal:
                return
            await asyncio.sleep(STREAM_POLL_SECONDS)

    async def _run_execution(
        self,
        session: AsyncSession,
        execution_id: int,
        graph: ExecutionGraphContext,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ) -> ExecutionOutputPayload:
        """Execute workflow nodes for an execution and return output payload.

        Args:
            session: Database session.
            execution_id: Execution ID.
            graph: Validated graph context.
            session_factory: When provided, independent branches run concurrently.

        Returns:
            Output payload.

        Raises:
            ExecutionNotFoundError: If execution is not found.
            WorkflowNotFoundError: If workflow is not found.
            ExecutionGraphValidationError: If graph is invalid.
            ExecutionInputValidationError: If input payload is invalid.

        """
        execution = await self._execution_repository.get_by(
            session=session,
            id=execution_id,
        )
        if execution is None:
            raise ExecutionNotFoundError

        workflow = await self._workflow_repository.get_by(
            session=session,
            id=execution.workflow_id,
        )
        if workflow is None:
            raise WorkflowNotFoundError

        run_context = _NodeRunContext(
            execution_id=execution_id,
            workflow_owner_id=workflow.owner_id,
            input_value=self._extract_input_value(input_data=execution.input_data),
        )

        if session_factory is None:
            outputs_by_node = await self._run_nodes_serial(
                session=session, run_context=run_context, graph=graph
            )
        else:
            outputs_by_node = await self._run_nodes_parallel(
                run_context=run_context, graph=graph, session_factory=session_factory
            )

        return ExecutionOutputPayload(value=outputs_by_node[graph.output_node_id])

    async def _run_nodes_serial(
        self,
        session: AsyncSession,
        run_context: _NodeRunContext,
        graph: ExecutionGraphContext,
    ) -> dict[int, str]:
        """Run nodes one at a time in topological order.

        Args:
            session: Database session shared by all nodes.
            run_context: Loop-invariant run context.
            graph: Validated graph context.

        Returns:
            Mapping of node ID to output text.

        """
        outputs_by_node: dict[int, str] = {}
        for node_id in graph.topological_order:
            node = graph.nodes_by_id[node_id]
            parent_values = [
                outputs_by_node[parent_id] for parent_id in graph.inbound[node_id]
            ]
            outputs_by_node[node_id] = await self._run_node(
                session=session,
                run_context=run_context,
                node=node,
                parent_values=parent_values,
            )

        return outputs_by_node

    async def _run_nodes_parallel(
        self,
        run_context: _NodeRunContext,
        graph: ExecutionGraphContext,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> dict[int, str]:
        """Run nodes wave by wave, concurrently within each wave.

        Each node runs on its own session so concurrent nodes never share one
        AsyncSession. A node becomes ready once all its parents have completed.

        Args:
            run_context: Loop-invariant run context.
            graph: Validated graph context.
            session_factory: Factory for per-node sessions.

        Returns:
            Mapping of node ID to output text.

        Raises:
            BaseError: If any node fails after exhausting its attempts.

        """
        indegree = {
            node_id: len(graph.inbound[node_id]) for node_id in graph.nodes_by_id
        }
        outputs_by_node: dict[int, str] = {}
        ready = [node_id for node_id, degree in indegree.items() if degree == 0]

        while ready:
            wave_results = await asyncio.gather(
                *(
                    self._run_node_isolated(
                        session_factory=session_factory,
                        run_context=run_context,
                        node=graph.nodes_by_id[node_id],
                        parent_values=[
                            outputs_by_node[parent_id]
                            for parent_id in graph.inbound[node_id]
                        ],
                    )
                    for node_id in ready
                ),
                return_exceptions=True,
            )
            for result in wave_results:
                if isinstance(result, BaseException):
                    raise result
                node_id, output = result
                outputs_by_node[node_id] = output

            next_ready: list[int] = []
            for node_id in ready:
                for child_id in graph.outbound[node_id]:
                    indegree[child_id] -= 1
                    if indegree[child_id] == 0:
                        next_ready.append(child_id)
            ready = next_ready

        return outputs_by_node

    async def _run_node_isolated(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        run_context: _NodeRunContext,
        node: NodeResponse,
        parent_values: list[str],
    ) -> tuple[int, str]:
        """Run one node on a dedicated session and return its ID and output.

        Args:
            session_factory: Factory for the node's own session.
            run_context: Loop-invariant run context.
            node: Node to execute.
            parent_values: Outputs of the node's parents.

        Returns:
            The node ID paired with its output text.

        """
        async with session_factory() as node_session:
            output = await self._run_node(
                session=node_session,
                run_context=run_context,
                node=node,
                parent_values=parent_values,
            )

        return node.id, output

    async def _run_node(
        self,
        session: AsyncSession,
        run_context: _NodeRunContext,
        node: NodeResponse,
        parent_values: list[str],
    ) -> str:
        """Run one node with retries, persisting its final result.

        Args:
            session: Database session.
            run_context: Loop-invariant run context.
            node: Node to execute.
            parent_values: Outputs of the node's parents.

        Returns:
            The node output text.

        Raises:
            BaseError: If the node fails after exhausting its attempts.

        """
        started_at = datetime.now(tz=UTC).replace(tzinfo=None)
        for attempt in range(1, self._max_node_attempts + 1):
            try:
                output = await self._run_node_once(
                    session=session,
                    run_context=run_context,
                    node=node,
                    parent_values=parent_values,
                )
            except BaseError as exc:
                if exc.retryable and attempt < self._max_node_attempts:
                    logger.warning(
                        "Node %s attempt %s failed (retryable): %s; retrying",
                        node.id,
                        attempt,
                        exc.message,
                    )
                    await asyncio.sleep(self._retry_delay(attempt=attempt))
                    continue

                await self._record_node_result(
                    session=session,
                    run_context=run_context,
                    node_id=node.id,
                    started_at=started_at,
                    outcome=_NodeOutcome(
                        status=ExecutionStatus.FAILED, error=exc.message
                    ),
                )
                raise

            await self._record_node_result(
                session=session,
                run_context=run_context,
                node_id=node.id,
                started_at=started_at,
                outcome=_NodeOutcome(status=ExecutionStatus.SUCCESS, output=output),
            )
            return output

        # Unreachable: the loop always returns or raises, but satisfies typing.
        message = f"Node {node.id} exhausted retries"
        raise ExecutionGraphValidationError(message=message)

    async def _run_node_once(
        self,
        session: AsyncSession,
        run_context: _NodeRunContext,
        node: NodeResponse,
        parent_values: list[str],
    ) -> str:
        """Execute a single node attempt within its time budget.

        Args:
            session: Database session.
            run_context: Loop-invariant run context.
            node: Node to execute.
            parent_values: Outputs of the node's parents.

        Returns:
            The node output text.

        Raises:
            ExecutionGraphValidationError: If a non-input node has no input.
            NodeExecutionTimeoutError: If the node exceeds its time budget.
            BaseError: If the node handler fails.

        """
        if node.type is not NodeType.INPUT and not parent_values:
            message = f"Node {node.id} does not have input value"
            raise ExecutionGraphValidationError(message=message)

        try:
            async with asyncio.timeout(self._node_timeout_seconds):
                return await self._node_registry.execute(
                    node_type=node.type,
                    context=NodeExecutionContext(
                        session=session,
                        workflow_owner_id=run_context.workflow_owner_id,
                        node_data=node.data,
                        parent_values=parent_values,
                        input_value=run_context.input_value,
                    ),
                )
        except TimeoutError as exc:
            raise NodeExecutionTimeoutError from exc

    async def _record_node_result(
        self,
        session: AsyncSession,
        run_context: _NodeRunContext,
        node_id: int,
        started_at: datetime,
        outcome: _NodeOutcome,
    ) -> None:
        """Persist a single node's result row.

        Args:
            session: Database session.
            run_context: Loop-invariant run context.
            node_id: Executed node ID.
            started_at: When the node started.
            outcome: The node's final status, output, and error.

        """
        await self._node_execution_repository.create(
            session=session,
            data={
                "execution_id": run_context.execution_id,
                "node_id": node_id,
                "status": outcome.status,
                "output": outcome.output,
                "error": outcome.error,
                "started_at": started_at,
                "finished_at": datetime.now(tz=UTC).replace(tzinfo=None),
            },
        )

    def _retry_delay(self, attempt: int) -> float:
        """Compute exponential backoff delay for a retry attempt.

        Args:
            attempt: The 1-based attempt number that just failed.

        Returns:
            Delay in seconds before the next attempt.

        """
        return RETRY_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))

    async def _mark_execution_success(
        self,
        session: AsyncSession,
        execution_id: int,
        output_data: ExecutionOutputPayload,
    ) -> ExecutionResponse:
        """Persist successful execution result.

        Args:
            session: Database session.
            execution_id: Execution ID.
            output_data: Final output payload.

        Returns:
            Updated execution.

        Raises:
            ExecutionNotFoundError: If execution record does not exist.

        """
        updated_execution = await self._execution_repository.update_by(
            session=session,
            id=execution_id,
            data={
                "status": ExecutionStatus.SUCCESS,
                "output_data": output_data.model_dump(),
                "error": None,
                "finished_at": datetime.now(tz=UTC).replace(tzinfo=None),
            },
        )
        if updated_execution is None:
            raise ExecutionNotFoundError

        return ExecutionResponse.model_validate(updated_execution)

    async def _mark_execution_failed(
        self,
        session: AsyncSession,
        execution_id: int,
        error: str,
    ) -> ExecutionResponse:
        """Persist failed execution result.

        Args:
            session: Database session.
            execution_id: Execution ID.
            error: Failure reason.

        Returns:
            Updated execution.

        Raises:
            ExecutionNotFoundError: If execution record does not exist.

        """
        updated_execution = await self._execution_repository.update_by(
            session=session,
            id=execution_id,
            data={
                "status": ExecutionStatus.FAILED,
                "error": error,
                "finished_at": datetime.now(tz=UTC).replace(tzinfo=None),
            },
        )
        if updated_execution is None:
            raise ExecutionNotFoundError

        return ExecutionResponse.model_validate(updated_execution)

    def _build_graph_context(
        self, nodes: list[NodeResponse], edges: list[EdgeResponse]
    ) -> ExecutionGraphContext:
        """Build and validate graph context for execution.

        Args:
            nodes: Workflow nodes.
            edges: Workflow edges.

        Returns:
            Validated graph context.

        Raises:
            ExecutionGraphValidationError: If graph is invalid.

        """
        if not nodes:
            message = "Workflow must contain at least one node"
            raise ExecutionGraphValidationError(message=message)

        input_nodes = [node for node in nodes if node.type is NodeType.INPUT]
        if len(input_nodes) != 1:
            message = "Workflow must contain exactly one input node"
            raise ExecutionGraphValidationError(message=message)

        output_nodes = [node for node in nodes if node.type is NodeType.OUTPUT]
        if len(output_nodes) != 1:
            message = "Workflow must contain exactly one output node"
            raise ExecutionGraphValidationError(message=message)

        nodes_by_id = {node.id: node for node in nodes}
        outbound: dict[int, list[int]] = {node.id: [] for node in nodes}
        inbound: dict[int, list[int]] = {node.id: [] for node in nodes}
        indegree: dict[int, int] = {node.id: 0 for node in nodes}
        for edge in edges:
            source_id = edge.source_node_id
            target_id = edge.target_node_id
            if source_id not in nodes_by_id or target_id not in nodes_by_id:
                message = "Workflow contains edge with missing node reference"
                raise ExecutionGraphValidationError(message=message)

            outbound[source_id].append(target_id)
            inbound[target_id].append(source_id)
            indegree[target_id] += 1

        topological_order = self._topological_order(
            indegree=indegree, outbound=outbound
        )
        input_node_id = input_nodes[0].id
        output_node_id = output_nodes[0].id
        self._validate_connectivity(
            input_node_id=input_node_id,
            output_node_id=output_node_id,
            outbound=outbound,
            inbound=inbound,
            nodes_by_id=nodes_by_id,
        )

        return ExecutionGraphContext(
            input_node_id=input_node_id,
            output_node_id=output_node_id,
            nodes_by_id=nodes_by_id,
            outbound=outbound,
            inbound=inbound,
            topological_order=topological_order,
        )

    def _topological_order(
        self,
        indegree: dict[int, int],
        outbound: dict[int, list[int]],
    ) -> list[int]:
        """Build topological order for workflow nodes.

        Args:
            indegree: Incoming edge count by node.
            outbound: Outbound adjacency map.

        Returns:
            Ordered node IDs.

        Raises:
            ExecutionGraphValidationError: If graph has a cycle.

        """
        queue: deque[int] = deque(
            node_id for node_id, node_indegree in indegree.items() if node_indegree == 0
        )
        order: list[int] = []
        seen_indegree = dict(indegree)
        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for target_id in outbound[node_id]:
                seen_indegree[target_id] -= 1
                if seen_indegree[target_id] == 0:
                    queue.append(target_id)

        if len(order) != len(indegree):
            message = "Workflow graph must be acyclic"
            raise ExecutionGraphValidationError(message=message)

        return order

    def _validate_connectivity(
        self,
        input_node_id: int,
        output_node_id: int,
        outbound: dict[int, list[int]],
        inbound: dict[int, list[int]],
        nodes_by_id: dict[int, NodeResponse],
    ) -> None:
        """Validate that every node is on a path from input to output.

        Args:
            input_node_id: Input node ID.
            output_node_id: Output node ID.
            outbound: Outbound adjacency map.
            inbound: Inbound adjacency map.
            nodes_by_id: Workflow nodes by ID.

        Raises:
            ExecutionGraphValidationError: If graph contains disconnected nodes.

        """
        for node_id in nodes_by_id:
            if node_id not in self._collect_reachable(
                start_node_id=input_node_id, adjacency=outbound
            ) or node_id not in self._collect_reachable(
                start_node_id=output_node_id, adjacency=inbound
            ):
                message = "All workflow nodes must belong to input->output path"
                raise ExecutionGraphValidationError(message=message)

    def _collect_reachable(
        self,
        start_node_id: int,
        adjacency: dict[int, list[int]],
    ) -> set[int]:
        """Collect reachable nodes using DFS.

        Args:
            start_node_id: Start node ID.
            adjacency: Adjacency map.

        Returns:
            Set of reachable node IDs.

        """
        stack = [start_node_id]
        visited: set[int] = set()
        while stack:
            node_id = stack.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            stack.extend(adjacency[node_id])
        return visited

    def _extract_input_value(self, input_data: dict | None) -> str:
        """Extract text input for input node execution.

        Args:
            input_data: Execution input payload.

        Returns:
            Input value.

        Raises:
            ExecutionInputValidationError: If payload is invalid.

        """
        if input_data is None:
            message = "Execution input payload is required"
            raise ExecutionInputValidationError(message=message)

        value = input_data.get("value")
        if not isinstance(value, str):
            message = "Execution input_data.value must be a string"
            raise ExecutionInputValidationError(message=message)

        return value
