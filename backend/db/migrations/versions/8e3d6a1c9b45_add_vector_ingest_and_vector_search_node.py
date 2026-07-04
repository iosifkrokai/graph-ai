"""Add vector_ingest and vector_search node types.

Revision ID: 8e3d6a1c9b45
Revises: 4c8b6d2a9f17
Create Date: 2026-07-05 10:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8e3d6a1c9b45"
down_revision: str | None = "4c8b6d2a9f17"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'VECTOR_INGEST'")
    op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'VECTOR_SEARCH'")


def downgrade() -> None:
    """Downgrade database schema.

    PostgreSQL enum values are not safely removable in-place, so this is a no-op.
    """
