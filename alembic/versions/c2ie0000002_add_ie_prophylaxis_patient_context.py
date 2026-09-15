"""add IE prophylaxis patient context fields

Revision ID: c2ie0000002
Revises: c1ctx0000001
Create Date: 2026-09-15
"""

from alembic import op
import sqlalchemy as sa


revision = "c2ie0000002"
down_revision = "c1ctx0000001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("penicillin_allergy_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("ie_cardiac_risk_category", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
    )


def downgrade():
    op.drop_column("patient_clinical_contexts", "ie_cardiac_risk_category")
    op.drop_column("patient_clinical_contexts", "penicillin_allergy_status")
