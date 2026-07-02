"""Add llm_provider api_key.

Revision ID: 709163b05319
Revises: afe93cec64d0
Create Date: 2026-07-02 20:46:38.407474

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "709163b05319"
down_revision: str | None = "afe93cec64d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade database schema."""
    op.add_column(
        "llm_providers",
        sa.Column(
            "api_key",
            sa.Text(),
            nullable=True,
            comment="Encrypted API key for cloud providers",
        ),
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.drop_column("llm_providers", "api_key")
