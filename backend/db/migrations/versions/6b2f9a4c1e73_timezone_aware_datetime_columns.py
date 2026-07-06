"""Make datetime columns timezone-aware.

Revision ID: 6b2f9a4c1e73
Revises: 4d8c2f0a7e91
Create Date: 2026-07-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b2f9a4c1e73"
down_revision: str | None = "4d8c2f0a7e91"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, column, nullable) for every naive `timestamp` column being
# converted to `timestamptz`. The app has always written these as UTC, so
# converting is a metadata-only reinterpretation, not a data rewrite.
_COLUMNS: list[tuple[str, str, bool]] = [
    ("users", "created_at", False),
    ("users", "updated_at", False),
    ("workflows", "created_at", False),
    ("workflows", "updated_at", False),
    ("workflow_versions", "created_at", False),
    ("workflow_versions", "updated_at", False),
    ("executions", "started_at", False),
    ("executions", "finished_at", True),
    ("executions", "heartbeat_at", True),
    ("node_executions", "started_at", False),
    ("node_executions", "finished_at", True),
]


def upgrade() -> None:
    """Upgrade database schema."""
    for table, column, nullable in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=nullable,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    """Downgrade database schema."""
    for table, column, nullable in _COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=nullable,
            postgresql_using=f"{column} AT TIME ZONE 'UTC'",
        )
