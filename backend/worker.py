"""ARQ worker for background workflow execution."""

import logging
from typing import Any, ClassVar

from arq import cron

from logging_config import configure_logging
from sessions import async_session
from settings import redis_settings
from usecases import ExecutionUsecase

logger = logging.getLogger(__name__)

# Reap stuck executions every 5 minutes.
_REAPER_MINUTES = set(range(0, 60, 5))


async def run_execution_task(ctx: dict[Any, Any], execution_id: int) -> None:
    """Run a workflow execution by ID on the worker.

    Args:
        ctx: ARQ job context.
        execution_id: The execution to run.

    """
    del ctx
    logger.info("Running execution %s", execution_id)
    async with async_session() as session:
        await ExecutionUsecase().run_execution(
            session=session,
            execution_id=execution_id,
            session_factory=async_session,
        )


async def reap_stuck_executions(
    ctx: dict[Any, Any], *args: object, **kwargs: object
) -> None:
    """Reap executions stuck in RUNNING beyond the timeout.

    Args:
        ctx: ARQ job context.
        args: Unused positional arguments (ARQ coroutine protocol).
        kwargs: Unused keyword arguments (ARQ coroutine protocol).

    """
    del ctx, args, kwargs
    async with async_session() as session:
        reaped = await ExecutionUsecase().reap_stuck_executions(session=session)
    if reaped:
        logger.warning("Reaped %s stuck execution(s)", reaped)


async def startup(ctx: dict[Any, Any]) -> None:
    """Configure logging when the worker starts.

    Args:
        ctx: ARQ job context.

    """
    del ctx
    configure_logging()


class WorkerSettings:
    """ARQ worker configuration."""

    functions: ClassVar[list] = [run_execution_task]
    cron_jobs: ClassVar[list] = [cron(reap_stuck_executions, minute=_REAPER_MINUTES)]
    redis_settings = redis_settings.arq
    on_startup = startup
