"""Add patient-scoped persistent odontograms.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_odontograms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("dentition_type", sa.String(length=16), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", name="uq_patient_odontograms_patient_id"),
    )
    op.create_index("ix_patient_odontograms_patient_id", "patient_odontograms", ["patient_id"], unique=True)
    op.create_index("ix_patient_odontograms_updated_by", "patient_odontograms", ["updated_by"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_patient_odontograms_updated_by", table_name="patient_odontograms")
    op.drop_index("ix_patient_odontograms_patient_id", table_name="patient_odontograms")
    op.drop_table("patient_odontograms")
