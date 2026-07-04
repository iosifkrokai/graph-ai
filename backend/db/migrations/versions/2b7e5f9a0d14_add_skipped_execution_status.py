"""Add skipped execution status.

Revision ID: 2b7e5f9a0d14
Revises: 9d4b6e2a1c73
Create Date: 2026-07-04 12:05:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b7e5f9a0d14"
down_revision: str | None = "9d4b6e2a1c73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.execute("ALTER TYPE executionstatus ADD VALUE IF NOT EXISTS 'SKIPPED'")


def downgrade() -> None:
    """Downgrade database schema.

    PostgreSQL enum values are not safely removable in-place, so this is a no-op.
    """
