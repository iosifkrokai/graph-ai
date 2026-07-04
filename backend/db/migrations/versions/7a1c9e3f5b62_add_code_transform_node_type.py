"""Add code_transform node type.

Revision ID: 7a1c9e3f5b62
Revises: 2b7e5f9a0d14
Create Date: 2026-07-04 12:10:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7a1c9e3f5b62"
down_revision: str | None = "2b7e5f9a0d14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'CODE_TRANSFORM'")


def downgrade() -> None:
    """Downgrade database schema.

    PostgreSQL enum values are not safely removable in-place, so this is a no-op.
    """
