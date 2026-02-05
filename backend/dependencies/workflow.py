"""Workflow dependency providers."""

from usecases import WorkflowUsecase


def get_workflow_usecase() -> WorkflowUsecase:
    """Get the workflow usecase."""
    return WorkflowUsecase()
