"""Add node_executions.

Revision ID: afe93cec64d0
Revises: 7f6f03f7f3a3
Create Date: 2026-07-02 12:31:35.890929

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "afe93cec64d0"
down_revision: str | None = "7f6f03f7f3a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_table(
        "node_executions",
        sa.Column(
            "execution_id",
            sa.Integer(),
            nullable=False,
            comment="Parent execution ID",
        ),
        sa.Column("node_id", sa.Integer(), nullable=False, comment="Executed node ID"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "CREATED",
                "RUNNING",
                "SUCCESS",
                "FAILED",
                name="executionstatus",
                create_type=False,
            ),
            nullable=False,
            comment="Node execution status",
        ),
        sa.Column(
            "output",
            sa.Text(),
            nullable=True,
            comment="Node output text if the node succeeded",
        ),
        sa.Column(
            "error",
            sa.Text(),
            nullable=True,
            comment="Error message if the node failed",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Node execution start time",
        ),
        sa.Column(
            "finished_at",
            sa.DateTime(),
            nullable=True,
            comment="Node execution end time",
        ),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="ID"),
        sa.ForeignKeyConstraint(
            ["execution_id"], ["executions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["node_id"], ["nodes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_table("node_executions")
