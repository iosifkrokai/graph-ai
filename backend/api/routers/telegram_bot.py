"""Telegram bot API routes."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import auth, db, telegram_bot
from schemas import (
    TelegramBotCreate,
    TelegramBotResponse,
    TelegramBotUpdate,
    UserResponse,
)

router = APIRouter(prefix="/telegram-bots", tags=["Telegram Bots"])


@router.post(path="")
async def create_telegram_bot(
    data: Annotated[
        TelegramBotCreate, Body(description="Data for creating a Telegram bot")
    ],
    session: Annotated[AsyncSession, Depends(dependency=db.get_session)],
    usecase: Annotated[
        telegram_bot.TelegramBotUsecase,
        Depends(dependency=telegram_bot.get_telegram_bot_usecase),
    ],
    current_user: Annotated[UserResponse, Depends(dependency=auth.get_current_user)],
) -> TelegramBotResponse:
    """Create a new Telegram bot."""
    return await usecase.create_telegram_bot(
        session=session, user_id=current_user.id, data=data
    )


@router.get(path="")
async def list_telegram_bots(
    session: Annotated[AsyncSession, Depends(dependency=db.get_session)],
    usecase: Annotated[
        telegram_bot.TelegramBotUsecase,
        Depends(dependency=telegram_bot.get_telegram_bot_usecase),
    ],
    current_user: Annotated[UserResponse, Depends(dependency=auth.get_current_user)],
) -> list[TelegramBotResponse]:
    """List Telegram bots for the current user."""
    return await usecase.get_telegram_bots(session=session, user_id=current_user.id)


@router.patch(path="/{bot_id}")
async def update_telegram_bot(
    bot_id: Annotated[int, Path(description="Telegram bot ID", gt=0)],
    data: Annotated[
        TelegramBotUpdate, Body(description="Data for updating a Telegram bot")
    ],
    session: Annotated[AsyncSession, Depends(dependency=db.get_session)],
    usecase: Annotated[
        telegram_bot.TelegramBotUsecase,
        Depends(dependency=telegram_bot.get_telegram_bot_usecase),
    ],
    current_user: Annotated[UserResponse, Depends(dependency=auth.get_current_user)],
) -> TelegramBotResponse:
    """Update a Telegram bot by ID."""
    return await usecase.update_telegram_bot(
        session=session, bot_id=bot_id, user_id=current_user.id, data=data
    )


@router.delete(path="/{bot_id}")
async def delete_telegram_bot(
    bot_id: Annotated[int, Path(description="Telegram bot ID", gt=0)],
    session: Annotated[AsyncSession, Depends(dependency=db.get_session)],
    usecase: Annotated[
        telegram_bot.TelegramBotUsecase,
        Depends(dependency=telegram_bot.get_telegram_bot_usecase),
    ],
    current_user: Annotated[UserResponse, Depends(dependency=auth.get_current_user)],
) -> JSONResponse:
    """Delete a Telegram bot by ID."""
    await usecase.delete_telegram_bot(
        session=session, bot_id=bot_id, user_id=current_user.id
    )
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED, content={"detail": "Telegram bot deleted"}
    )
