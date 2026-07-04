"""Add Telegram bots.

Revision ID: f2a4c8e6b1d3
Revises: e4f1a9c2b7d8
Create Date: 2026-07-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2a4c8e6b1d3"
down_revision: str | None = "e4f1a9c2b7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "telegram_bots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("bot_token", sa.Text(), nullable=False),
        sa.Column(
            "last_update_id",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_telegram_bots_user_id", "telegram_bots", ["user_id"])
    op.add_column(
        "executions",
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column("executions", "telegram_chat_id")
    op.drop_index("ix_telegram_bots_user_id", table_name="telegram_bots")
    op.drop_table("telegram_bots")
