"""Usecase logic for workflows."""

from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import ResourceNotFoundError
from repositories import UserRepository, WorkflowRepository
from schemas import WorkflowCreate, WorkflowResponse, WorkflowUpdate


class WorkflowUsecase:
    """Usecase operations for workflows."""

    def __init__(self) -> None:
        """Initialize repositories for workflow operations."""
        self._workflow_repository = WorkflowRepository()
        self._user_repository = UserRepository()

    async def create_workflow(
        self, session: AsyncSession, data: WorkflowCreate
    ) -> WorkflowResponse:
        """Create a workflow for a user."""
        owner = await self._user_repository.get_by(session=session, id=data.owner_id)
        if not owner:
            resource = "User"
            raise ResourceNotFoundError(resource)

        workflow = await self._workflow_repository.create(
            session=session,
            data={"owner_id": data.owner_id, "name": data.name},
        )
        return WorkflowResponse.model_validate(workflow)

    async def get_workflows(
        self, session: AsyncSession, owner_id: int | None = None
    ) -> list[WorkflowResponse]:
        """List workflows, optionally filtered by owner."""
        filters = {"owner_id": owner_id} if owner_id else {}
        return [
            WorkflowResponse.model_validate(workflow)
            for workflow in await self._workflow_repository.get_all(
                session=session, **filters
            )
        ]

    async def get_workflow(
        self, session: AsyncSession, workflow_id: int
    ) -> WorkflowResponse:
        """Fetch a workflow by ID."""
        workflow = await self._workflow_repository.get_by(
            session=session, id=workflow_id
        )
        if not workflow:
            resource = "Workflow"
            raise ResourceNotFoundError(resource)
        return WorkflowResponse.model_validate(workflow)

    async def update_workflow(
        self, session: AsyncSession, workflow_id: int, data: WorkflowUpdate
    ) -> WorkflowResponse:
        """Update a workflow by ID."""
        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        if not update_data:
            return await self.get_workflow(session=session, workflow_id=workflow_id)

        workflow = await self._workflow_repository.update_by(
            session=session,
            data=update_data,
            id=workflow_id,
        )
        if not workflow:
            resource = "Workflow"
            raise ResourceNotFoundError(resource)
        return WorkflowResponse.model_validate(workflow)

    async def delete_workflow(self, session: AsyncSession, workflow_id: int) -> None:
        """Delete a workflow by ID."""
        deleted = await self._workflow_repository.delete_by(
            session=session, id=workflow_id
        )
        if not deleted:
            resource = "Workflow"
            raise ResourceNotFoundError(resource)
