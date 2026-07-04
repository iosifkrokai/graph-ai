"""Telegram bot model."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.models import BaseWithID


class TelegramBot(BaseWithID):
    """A user's Telegram bot, referenced by Input/Output nodes by ID.

    Mirrors :class:`LLMProvider`: a reusable, user-owned credential that nodes
    reference by ID rather than embed inline.
    """

    __tablename__ = "telegram_bots"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID",
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Bot display name",
    )
    bot_token: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Encrypted Telegram bot token",
    )
    last_update_id: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        comment="Highest Telegram update_id processed so far",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        comment="Whether polling is active for this bot",
    )
