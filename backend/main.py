"""Backend entrypoint."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from exceptions import BaseError
from routers import (
    edge,
    execution,
    health,
    input_node,
    llm_node,
    llm_provider,
    node,
    output_node,
    user,
    workflow,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Graph AI Backend")


@app.exception_handler(BaseError)
async def handle_base_error(_: Request, exc: BaseError) -> JSONResponse:
    """Convert domain errors into JSON responses."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


app.include_router(health.router)
app.include_router(user.router)
app.include_router(workflow.router)
app.include_router(node.router)
app.include_router(edge.router)
app.include_router(execution.router)
app.include_router(llm_provider.router)
app.include_router(input_node.router)
app.include_router(llm_node.router)
app.include_router(output_node.router)
