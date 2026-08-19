"""add recoverable imaging trash records

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "imaging_trash_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("modality", sa.String(length=16), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("deleted_by", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("modality", "analysis_id", name="uq_imaging_trash_modality_analysis"),
    )
    op.create_index("ix_imaging_trash_records_id", "imaging_trash_records", ["id"], unique=False)
    op.create_index("ix_imaging_trash_records_modality", "imaging_trash_records", ["modality"], unique=False)
    op.create_index("ix_imaging_trash_records_analysis_id", "imaging_trash_records", ["analysis_id"], unique=False)
    op.create_index("ix_imaging_trash_records_patient_id", "imaging_trash_records", ["patient_id"], unique=False)
    op.create_index("ix_imaging_trash_records_deleted_by", "imaging_trash_records", ["deleted_by"], unique=False)
    op.create_index("ix_imaging_trash_records_deleted_at", "imaging_trash_records", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_imaging_trash_records_deleted_at", table_name="imaging_trash_records")
    op.drop_index("ix_imaging_trash_records_deleted_by", table_name="imaging_trash_records")
    op.drop_index("ix_imaging_trash_records_patient_id", table_name="imaging_trash_records")
    op.drop_index("ix_imaging_trash_records_analysis_id", table_name="imaging_trash_records")
    op.drop_index("ix_imaging_trash_records_modality", table_name="imaging_trash_records")
    op.drop_index("ix_imaging_trash_records_id", table_name="imaging_trash_records")
    op.drop_table("imaging_trash_records")
