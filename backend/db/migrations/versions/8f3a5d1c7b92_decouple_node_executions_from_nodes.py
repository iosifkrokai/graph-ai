"""Decouple node_executions from live nodes.

Revision ID: 8f3a5d1c7b92
Revises: 6b2f9a4c1e73
Create Date: 2026-07-06 01:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8f3a5d1c7b92"
down_revision: str | None = "6b2f9a4c1e73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    # `node_id` stays as a plain historical reference: a pinned execution can
    # rerun a workflow-version snapshot referencing a node since deleted from
    # the live `nodes` table, which an enforced FK would reject on insert.
    # Dropping it also means deleting a node no longer cascades-deletes its
    # (unrelated) execution history.
    op.drop_constraint(
        "node_executions_node_id_fkey", "node_executions", type_="foreignkey"
    )
    op.add_column(
        "node_executions",
        sa.Column(
            "node_type",
            postgresql.ENUM(name="nodetype", create_type=False),
            nullable=True,
            comment="Node type at execution time (denormalized snapshot)",
        ),
    )
    op.add_column(
        "node_executions",
        sa.Column(
            "node_label",
            sa.Text(),
            nullable=True,
            comment="Node label at execution time (denormalized snapshot)",
        ),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column("node_executions", "node_label")
    op.drop_column("node_executions", "node_type")
    op.create_foreign_key(
        "node_executions_node_id_fkey",
        "node_executions",
        "nodes",
        ["node_id"],
        ["id"],
        ondelete="CASCADE",
    )
