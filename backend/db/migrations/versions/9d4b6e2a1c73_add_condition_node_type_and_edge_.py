"""Add condition node type and edge source_handle.

Revision ID: 9d4b6e2a1c73
Revises: f2a4c8e6b1d3
Create Date: 2026-07-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d4b6e2a1c73"
down_revision: str | None = "f2a4c8e6b1d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'CONDITION'")
    op.add_column(
        "edges",
        sa.Column("source_handle", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade database schema.

    PostgreSQL enum values are not safely removable in-place, so only the
    added column is dropped.
    """
    op.drop_column("edges", "source_handle")
