"""Add execution heartbeat_at column.

Revision ID: 4d8c2f0a7e91
Revises: 9a1f4c7e2b83
Create Date: 2026-07-05 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d8c2f0a7e91"
down_revision: str | None = "9a1f4c7e2b83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COMMENT = (
    "Last node-completion time, bumped as the run progresses so the "
    "stuck-execution reaper can tell a long-but-active run from one "
    "that's actually stalled"
)


def upgrade() -> None:
    """Upgrade database schema."""
    op.add_column(
        "executions",
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True, comment=_COMMENT),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column("executions", "heartbeat_at")
