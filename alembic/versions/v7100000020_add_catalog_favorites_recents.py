"""Add favorites and recent-use metadata to central cabinet catalog acts.

Revision ID: v7100000020
Revises: v7100000019
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "v7100000020"
down_revision: Union[str, Sequence[str], None] = "v7100000019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cabinet_catalog_acts",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "cabinet_catalog_acts",
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "cabinet_catalog_acts",
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cabinet_catalog_acts", "last_used_at")
    op.drop_column("cabinet_catalog_acts", "usage_count")
    op.drop_column("cabinet_catalog_acts", "is_favorite")
