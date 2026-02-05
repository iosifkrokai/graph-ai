"""LLM provider API routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import db
from dependencies import llm_provider as llm_provider_dependency
from schemas import LLMProviderCreate, LLMProviderResponse, LLMProviderUpdate
from usecases import LLMProviderUsecase

router = APIRouter(prefix="/llm-providers", tags=["LLM Providers"])


@router.post(path="", status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: Annotated[LLMProviderCreate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMProviderUsecase, Depends(llm_provider_dependency.get_llm_provider_usecase)
    ],
) -> LLMProviderResponse:
    """Create a new LLM provider."""
    return await usecase.create_provider(session=session, data=data)


@router.get(path="")
async def list_providers(
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMProviderUsecase, Depends(llm_provider_dependency.get_llm_provider_usecase)
    ],
    user_id: Annotated[int | None, Query()] = None,
) -> list[LLMProviderResponse]:
    """List LLM providers, optionally filtered by user."""
    return await usecase.get_providers(session=session, user_id=user_id)


@router.get(path="/{provider_id}")
async def get_provider(
    provider_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMProviderUsecase, Depends(llm_provider_dependency.get_llm_provider_usecase)
    ],
) -> LLMProviderResponse:
    """Fetch an LLM provider by ID."""
    return await usecase.get_provider(session=session, provider_id=provider_id)


@router.patch(path="/{provider_id}")
async def update_provider(
    provider_id: Annotated[int, Path(default=..., gt=0)],
    data: Annotated[LLMProviderUpdate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMProviderUsecase, Depends(llm_provider_dependency.get_llm_provider_usecase)
    ],
) -> LLMProviderResponse:
    """Update an LLM provider by ID."""
    return await usecase.update_provider(
        session=session, provider_id=provider_id, data=data
    )


@router.delete(path="/{provider_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_provider(
    provider_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[
        LLMProviderUsecase, Depends(llm_provider_dependency.get_llm_provider_usecase)
    ],
) -> JSONResponse:
    """Delete an LLM provider by ID."""
    await usecase.delete_provider(session=session, provider_id=provider_id)
    return JSONResponse(content={"detail": "LLM provider deleted"})
