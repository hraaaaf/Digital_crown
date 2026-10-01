"""add N4.3B backoffice antithrombotic context

Revision ID: neo000000025
Revises: neo000000024
Create Date: 2026-10-01
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000025"
down_revision = "neo000000024"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("anticoagulant_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("anticoagulants", sa.JSON(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("antiplatelet_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("antiplatelets", sa.JSON(), nullable=True))
    op.add_column("patient_clinical_contexts", sa.Column("antithrombotic_classes", sa.JSON(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("antithrombotic_combination_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("warfarin_inr", sa.Float(), nullable=True))
    op.add_column("patient_clinical_contexts", sa.Column("warfarin_inr_checked_at", sa.DateTime(), nullable=True))
    op.add_column("patient_clinical_contexts", sa.Column("warfarin_inr_current", sa.Boolean(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("lmwh_dose_class", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )


def downgrade():
    op.drop_column("patient_clinical_contexts", "lmwh_dose_class")
    op.drop_column("patient_clinical_contexts", "warfarin_inr_current")
    op.drop_column("patient_clinical_contexts", "warfarin_inr_checked_at")
    op.drop_column("patient_clinical_contexts", "warfarin_inr")
    op.drop_column("patient_clinical_contexts", "antithrombotic_combination_status")
    op.drop_column("patient_clinical_contexts", "antithrombotic_classes")
    op.drop_column("patient_clinical_contexts", "antiplatelets")
    op.drop_column("patient_clinical_contexts", "antiplatelet_status")
    op.drop_column("patient_clinical_contexts", "anticoagulants")
    op.drop_column("patient_clinical_contexts", "anticoagulant_status")
