"""Add trusted workstation mode memory and owner PIN policy.

Revision ID: v7100000021
Revises: v7100000020
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "v7100000021"
down_revision: Union[str, Sequence[str], None] = "v7100000020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workstation_security_policies",
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("owner_pin_hash", sa.String(length=255), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "workstation_modes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("default_experience", sa.String(length=32), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "default_experience IS NULL OR default_experience IN ('cabinet','station','control_center')",
            name="ck_workstation_default_experience",
        ),
    )
    op.create_index("ix_workstation_modes_employer_id", "workstation_modes", ["employer_id"])


def downgrade() -> None:
    op.drop_index("ix_workstation_modes_employer_id", table_name="workstation_modes")
    op.drop_table("workstation_modes")
    op.drop_table("workstation_security_policies")
