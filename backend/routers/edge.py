"""Edge API routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import db
from dependencies import edge as edge_dependency
from schemas import EdgeCreate, EdgeResponse, EdgeUpdate
from usecases import EdgeUsecase

router = APIRouter(prefix="/edges", tags=["Edges"])


@router.post(path="", status_code=status.HTTP_201_CREATED)
async def create_edge(
    data: Annotated[EdgeCreate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[EdgeUsecase, Depends(edge_dependency.get_edge_usecase)],
) -> EdgeResponse:
    """Create a new edge."""
    return await usecase.create_edge(session=session, data=data)


@router.get(path="")
async def list_edges(
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[EdgeUsecase, Depends(edge_dependency.get_edge_usecase)],
    workflow_id: Annotated[int | None, Query()] = None,
) -> list[EdgeResponse]:
    """List edges, optionally filtered by workflow."""
    return await usecase.get_edges(session=session, workflow_id=workflow_id)


@router.get(path="/{edge_id}")
async def get_edge(
    edge_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[EdgeUsecase, Depends(edge_dependency.get_edge_usecase)],
) -> EdgeResponse:
    """Fetch a single edge by ID."""
    return await usecase.get_edge(session=session, edge_id=edge_id)


@router.patch(path="/{edge_id}")
async def update_edge(
    edge_id: Annotated[int, Path(default=..., gt=0)],
    data: Annotated[EdgeUpdate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[EdgeUsecase, Depends(edge_dependency.get_edge_usecase)],
) -> EdgeResponse:
    """Update an edge by ID."""
    return await usecase.update_edge(session=session, edge_id=edge_id, data=data)


@router.delete(path="/{edge_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_edge(
    edge_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[EdgeUsecase, Depends(edge_dependency.get_edge_usecase)],
) -> JSONResponse:
    """Delete an edge by ID."""
    await usecase.delete_edge(session=session, edge_id=edge_id)
    return JSONResponse(content={"detail": "Edge deleted"})
