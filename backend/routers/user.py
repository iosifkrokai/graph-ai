"""User API routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import db
from dependencies import user as user_dependency
from schemas import UserCreate, UserResponse, UserUpdate
from usecases import UserUsecase

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(path="", status_code=status.HTTP_201_CREATED)
async def create_user(
    data: Annotated[UserCreate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[UserUsecase, Depends(user_dependency.get_user_usecase)],
) -> UserResponse:
    """Create a user."""
    return await usecase.create_user(session=session, data=data)


@router.get(path="")
async def list_users(
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[UserUsecase, Depends(user_dependency.get_user_usecase)],
) -> list[UserResponse]:
    """List all users."""
    return await usecase.get_users(session=session)


@router.get(path="/{user_id}")
async def get_user(
    user_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[UserUsecase, Depends(user_dependency.get_user_usecase)],
) -> UserResponse:
    """Fetch a user by ID."""
    return await usecase.get_user(session=session, user_id=user_id)


@router.patch(path="/{user_id}")
async def update_user(
    user_id: Annotated[int, Path(default=..., gt=0)],
    data: Annotated[UserUpdate, Body(default=...)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[UserUsecase, Depends(user_dependency.get_user_usecase)],
) -> UserResponse:
    """Update a user by ID."""
    return await usecase.update_user(session=session, user_id=user_id, data=data)


@router.delete(path="/{user_id}", status_code=status.HTTP_202_ACCEPTED)
async def delete_user(
    user_id: Annotated[int, Path(default=..., gt=0)],
    session: Annotated[AsyncSession, Depends(db.get_session)],
    usecase: Annotated[UserUsecase, Depends(user_dependency.get_user_usecase)],
) -> JSONResponse:
    """Delete a user by ID."""
    await usecase.delete_user(session=session, user_id=user_id)
    return JSONResponse(content={"detail": "User deleted"})
