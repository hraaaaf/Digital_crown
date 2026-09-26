"""Add per-practitioner favorites and recent-use metadata for catalog acts.

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
    op.create_table(
        "cabinet_catalog_act_preferences",
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("act_id", sa.Integer(), sa.ForeignKey("cabinet_catalog_acts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_catalog_act_preferences_employer",
        "cabinet_catalog_act_preferences",
        ["employer_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_catalog_act_preferences_employer", table_name="cabinet_catalog_act_preferences")
    op.drop_table("cabinet_catalog_act_preferences")
