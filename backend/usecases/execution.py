"""Usecase logic for executions."""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from enums import ExecutionStatus
from exceptions import ResourceNotFoundError
from repositories import ExecutionRepository, WorkflowRepository
from schemas import ExecutionCreate, ExecutionResponse, ExecutionUpdate


class ExecutionUsecase:
    """Usecase operations for executions."""

    def __init__(self) -> None:
        """Initialize repositories for execution operations."""
        self._execution_repository = ExecutionRepository()
        self._workflow_repository = WorkflowRepository()

    async def create_execution(
        self, session: AsyncSession, data: ExecutionCreate
    ) -> ExecutionResponse:
        """Create an execution for a workflow."""
        workflow = await self._workflow_repository.get_by(
            session=session, id=data.workflow_id
        )
        if not workflow:
            resource = "Workflow"
            raise ResourceNotFoundError(resource)

        payload: dict[str, object] = {
            "workflow_id": data.workflow_id,
            "input_data": data.input_data,
        }
        if data.status is not None:
            payload["status"] = data.status

        execution = await self._execution_repository.create(
            session=session,
            data=payload,
        )
        return ExecutionResponse.model_validate(execution)

    async def get_executions(
        self, session: AsyncSession, workflow_id: int | None = None
    ) -> list[ExecutionResponse]:
        """List executions, optionally filtered by workflow."""
        filters = {"workflow_id": workflow_id} if workflow_id else {}
        return [
            ExecutionResponse.model_validate(execution)
            for execution in await self._execution_repository.get_all(
                session=session, **filters
            )
        ]

    async def get_execution(
        self, session: AsyncSession, execution_id: int
    ) -> ExecutionResponse:
        """Fetch an execution by ID."""
        execution = await self._execution_repository.get_by(
            session=session, id=execution_id
        )
        if not execution:
            resource = "Execution"
            raise ResourceNotFoundError(resource)
        return ExecutionResponse.model_validate(execution)

    async def update_execution(
        self, session: AsyncSession, execution_id: int, data: ExecutionUpdate
    ) -> ExecutionResponse:
        """Update an execution by ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_execution(session=session, execution_id=execution_id)

        status = update_data.get("status")
        if status in {ExecutionStatus.SUCCESS, ExecutionStatus.FAILED}:
            update_data.setdefault("finished_at", datetime.now(tz=UTC))

        execution = await self._execution_repository.update_by(
            session=session,
            data=update_data,
            id=execution_id,
        )
        if not execution:
            resource = "Execution"
            raise ResourceNotFoundError(resource)
        return ExecutionResponse.model_validate(execution)

    async def delete_execution(self, session: AsyncSession, execution_id: int) -> None:
        """Delete an execution by ID."""
        deleted = await self._execution_repository.delete_by(
            session=session, id=execution_id
        )
        if not deleted:
            resource = "Execution"
            raise ResourceNotFoundError(resource)
