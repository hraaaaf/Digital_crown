"""add master plan revision history

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "treatment_master_plan_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("steps_snapshot", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["treatment_master_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id", "revision", name="uq_master_plan_revision"),
    )
    op.create_index("ix_treatment_master_plan_revisions_id", "treatment_master_plan_revisions", ["id"], unique=False)
    op.create_index("ix_treatment_master_plan_revisions_plan_id", "treatment_master_plan_revisions", ["plan_id"], unique=False)
    op.create_index("ix_treatment_master_plan_revisions_patient_id", "treatment_master_plan_revisions", ["patient_id"], unique=False)
    op.create_index("ix_treatment_master_plan_revisions_updated_by", "treatment_master_plan_revisions", ["updated_by"], unique=False)
    op.create_index("ix_treatment_master_plan_revisions_created_at", "treatment_master_plan_revisions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_treatment_master_plan_revisions_created_at", table_name="treatment_master_plan_revisions")
    op.drop_index("ix_treatment_master_plan_revisions_updated_by", table_name="treatment_master_plan_revisions")
    op.drop_index("ix_treatment_master_plan_revisions_patient_id", table_name="treatment_master_plan_revisions")
    op.drop_index("ix_treatment_master_plan_revisions_plan_id", table_name="treatment_master_plan_revisions")
    op.drop_index("ix_treatment_master_plan_revisions_id", table_name="treatment_master_plan_revisions")
    op.drop_table("treatment_master_plan_revisions")
