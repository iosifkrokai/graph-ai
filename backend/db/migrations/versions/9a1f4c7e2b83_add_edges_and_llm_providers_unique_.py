"""Add edges and llm_providers unique constraints.

Revision ID: 9a1f4c7e2b83
Revises: 8e3d6a1c9b45
Create Date: 2026-07-05 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a1f4c7e2b83"
down_revision: str | None = "8e3d6a1c9b45"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.create_unique_constraint(
        "uq_edges_workflow_source_target",
        "edges",
        ["workflow_id", "source_node_id", "target_node_id"],
    )
    op.create_unique_constraint(
        "uq_llm_providers_user_name",
        "llm_providers",
        ["user_id", "name"],
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_constraint("uq_llm_providers_user_name", "llm_providers", type_="unique")
    op.drop_constraint("uq_edges_workflow_source_target", "edges", type_="unique")
