"""Sync missing column comments.

A few earlier migrations (workflow_versions, telegram_bots, the executions
version_id/telegram_chat_id/edges source_handle columns) never set the
``comment=`` DDL that their SQLAlchemy model columns declare, so `alembic
check` flags perpetual drift between models and the live schema. This
migration brings the DB comments in line with the models without changing
any types/nullability/defaults.

Revision ID: 4c8b6d2a9f17
Revises: 7a1c9e3f5b62
Create Date: 2026-07-05 09:00:00.000000

"""

from collections.abc import Sequence
from typing import Any, NamedTuple

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4c8b6d2a9f17"
down_revision: str | None = "7a1c9e3f5b62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


class _ColumnComment(NamedTuple):
    """A column that's missing its model-declared comment in the live schema."""

    table: str
    column: str
    existing_type: sa.types.TypeEngine
    existing_nullable: bool
    existing_server_default: Any
    comment: str


_COMMENTS: list[_ColumnComment] = [
    _ColumnComment(
        table="edges",
        column="source_handle",
        existing_type=sa.String(),
        existing_nullable=True,
        existing_server_default=None,
        comment="Named output handle on the source node (None = default handle)",
    ),
    _ColumnComment(
        table="executions",
        column="version_id",
        existing_type=sa.Integer(),
        existing_nullable=True,
        existing_server_default=None,
        comment="Pinned workflow version snapshot",
    ),
    _ColumnComment(
        table="executions",
        column="telegram_chat_id",
        existing_type=sa.BigInteger(),
        existing_nullable=True,
        existing_server_default=None,
        comment="Telegram chat to reply to, if this run was triggered by a message",
    ),
    _ColumnComment(
        table="telegram_bots",
        column="id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_server_default=None,
        comment="ID",
    ),
    _ColumnComment(
        table="telegram_bots",
        column="user_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_server_default=None,
        comment="Owner user ID",
    ),
    _ColumnComment(
        table="telegram_bots",
        column="name",
        existing_type=sa.String(length=128),
        existing_nullable=False,
        existing_server_default=None,
        comment="Bot display name",
    ),
    _ColumnComment(
        table="telegram_bots",
        column="bot_token",
        existing_type=sa.Text(),
        existing_nullable=False,
        existing_server_default=None,
        comment="Encrypted Telegram bot token",
    ),
    _ColumnComment(
        table="telegram_bots",
        column="last_update_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_server_default="0",
        comment="Highest Telegram update_id processed so far",
    ),
    _ColumnComment(
        table="telegram_bots",
        column="enabled",
        existing_type=sa.Boolean(),
        existing_nullable=False,
        existing_server_default="true",
        comment="Whether polling is active for this bot",
    ),
    _ColumnComment(
        table="workflow_versions",
        column="id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_server_default=None,
        comment="ID",
    ),
    _ColumnComment(
        table="workflow_versions",
        column="created_at",
        existing_type=sa.DateTime(),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
        comment="Created at",
    ),
    _ColumnComment(
        table="workflow_versions",
        column="updated_at",
        existing_type=sa.DateTime(),
        existing_nullable=False,
        existing_server_default=sa.text("now()"),
        comment="Updated at",
    ),
    _ColumnComment(
        table="workflow_versions",
        column="workflow_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_server_default=None,
        comment="Parent workflow ID",
    ),
    _ColumnComment(
        table="workflow_versions",
        column="version",
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_server_default=None,
        comment="Per-workflow incrementing version number",
    ),
    _ColumnComment(
        table="workflow_versions",
        column="graph",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        existing_nullable=False,
        existing_server_default=None,
        comment="Snapshot of the graph: {'nodes': [...], 'edges': [...]}",
    ),
]


def upgrade() -> None:
    """Upgrade database schema."""
    for entry in _COMMENTS:
        op.alter_column(
            entry.table,
            entry.column,
            existing_type=entry.existing_type,
            existing_nullable=entry.existing_nullable,
            existing_server_default=entry.existing_server_default,
            comment=entry.comment,
        )


def downgrade() -> None:
    """Downgrade database schema."""
    for entry in _COMMENTS:
        op.alter_column(
            entry.table,
            entry.column,
            existing_type=entry.existing_type,
            existing_nullable=entry.existing_nullable,
            existing_server_default=entry.existing_server_default,
            comment=None,
        )
