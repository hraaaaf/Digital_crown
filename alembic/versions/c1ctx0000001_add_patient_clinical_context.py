"""add patient clinical context

Revision ID: c1ctx0000001
Revises: f5a55e700005
Create Date: 2026-09-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1ctx0000001"
down_revision: Union[str, None] = "f5a55e700005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_clinical_contexts",
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("medication_allergy_status", sa.String(length=32), server_default="UNKNOWN", nullable=False),
        sa.Column("medication_allergies", sa.JSON(), nullable=True),
        sa.Column("renal_context_status", sa.String(length=32), server_default="UNKNOWN", nullable=False),
        sa.Column("renal_context_note", sa.Text(), nullable=True),
        sa.Column("hepatic_context_status", sa.String(length=32), server_default="UNKNOWN", nullable=False),
        sa.Column("hepatic_context_note", sa.Text(), nullable=True),
        sa.Column("prescription_indication", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("patient_id"),
    )
    op.create_index(
        op.f("ix_patient_clinical_contexts_employer_id"),
        "patient_clinical_contexts",
        ["employer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_patient_clinical_contexts_employer_id"), table_name="patient_clinical_contexts")
    op.drop_table("patient_clinical_contexts")
