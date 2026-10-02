"""add neo ordonnance rx context fields

Revision ID: neo000000023
Revises: v7100000022
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000023"
down_revision = "v7100000022"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("patient_clinical_contexts", sa.Column("pregnancy_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"))
    op.add_column("patient_clinical_contexts", sa.Column("breastfeeding_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"))
    op.add_column("patient_clinical_contexts", sa.Column("current_medications_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"))
    op.add_column("patient_clinical_contexts", sa.Column("current_medications", sa.JSON(), nullable=True))


def downgrade():
    op.drop_column("patient_clinical_contexts", "current_medications")
    op.drop_column("patient_clinical_contexts", "current_medications_status")
    op.drop_column("patient_clinical_contexts", "breastfeeding_status")
    op.drop_column("patient_clinical_contexts", "pregnancy_status")
