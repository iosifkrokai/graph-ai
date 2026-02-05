"""LLM node API routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import db
from dependencies import llm_node as llm_node_dependency
from schemas import LLMNodeCreate, LLMNodeResponse, LLMNodeUpdate
from usecases import LLMNodeUsecase

router = APIRouter(prefix="/llm-nodes", tags=["LLM Nodes"])


@router.post(path="", status_code=status.HTTP_201_CREATED)
async def create_llm_node(
    data: Annotated[LLMNodeCreate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMNodeUsecase, Depends(llm_node_dependency.get_llm_node_usecase)
    ],
) -> LLMNodeResponse:
    """Create an LLM node configuration."""
    return await usecase.create_llm_node(session=session, data=data)


@router.get(path="/{node_id}")
async def get_llm_node(
    node_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMNodeUsecase, Depends(llm_node_dependency.get_llm_node_usecase)
    ],
) -> LLMNodeResponse:
    """Fetch an LLM node configuration by node ID."""
    return await usecase.get_llm_node(session=session, node_id=node_id)


@router.patch(path="/{node_id}")
async def update_llm_node(
    node_id: Annotated[int, Path(default=..., gt=0)],
    data: Annotated[LLMNodeUpdate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMNodeUsecase, Depends(llm_node_dependency.get_llm_node_usecase)
    ],
) -> LLMNodeResponse:
    """Update an LLM node configuration by node ID."""
    return await usecase.update_llm_node(session=session, node_id=node_id, data=data)


@router.delete(path="/{node_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_llm_node(
    node_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMNodeUsecase, Depends(llm_node_dependency.get_llm_node_usecase)
    ],
) -> JSONResponse:
    """Delete an LLM node configuration by node ID."""
    await usecase.delete_llm_node(session=session, node_id=node_id)
    return JSONResponse(content={"detail": "LLM node deleted"})
