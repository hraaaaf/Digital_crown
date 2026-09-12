"""add patient practitioner assignment

Revision ID: e4a55e700004
Revises: d3a55e700003
Create Date: 2026-09-12

Additive-only P2 migration. The canonical patients table and document archive are not
rewritten or backfilled.
"""
from alembic import op
import sqlalchemy as sa


revision = "e4a55e700004"
down_revision = "d3a55e700003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_practitioner_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("practitioner_id", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["practitioner_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("patient_id", name="uq_patient_practitioner_assignment_patient"),
    )
    op.create_index("ix_patient_practitioner_assignments_patient_id", "patient_practitioner_assignments", ["patient_id"], unique=False)
    op.create_index("ix_patient_practitioner_assignments_employer_id", "patient_practitioner_assignments", ["employer_id"], unique=False)
    op.create_index("ix_patient_practitioner_assignments_practitioner_id", "patient_practitioner_assignments", ["practitioner_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_patient_practitioner_assignments_practitioner_id", table_name="patient_practitioner_assignments")
    op.drop_index("ix_patient_practitioner_assignments_employer_id", table_name="patient_practitioner_assignments")
    op.drop_index("ix_patient_practitioner_assignments_patient_id", table_name="patient_practitioner_assignments")
    op.drop_table("patient_practitioner_assignments")
