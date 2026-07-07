"""Sync node_executions.node_id comment.

Revision ID: f171aa16e4f5
Revises: 8f3a5d1c7b92
Create Date: 2026-07-07 18:13:03.571857

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f171aa16e4f5"
down_revision: str | None = "8f3a5d1c7b92"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_COMMENT = "Executed node ID (not FK-enforced; the node may since be deleted)"
_OLD_COMMENT = "Executed node ID"


def upgrade() -> None:
    """Upgrade database schema."""
    op.alter_column(
        "node_executions",
        "node_id",
        existing_type=sa.INTEGER(),
        comment=_NEW_COMMENT,
        existing_comment=_OLD_COMMENT,
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.alter_column(
        "node_executions",
        "node_id",
        existing_type=sa.INTEGER(),
        comment=_OLD_COMMENT,
        existing_comment=_NEW_COMMENT,
        existing_nullable=False,
    )
