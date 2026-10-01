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
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("mronj_medication_status", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("mronj_agents", sa.JSON(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("mronj_agent_class", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("mronj_indication", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("mronj_route", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("mronj_duration_months", sa.Integer(), nullable=True))
    op.add_column("patient_clinical_contexts", sa.Column("mronj_concurrent_risk_therapy", sa.JSON(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("active_oral_infection_or_inflammation", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("suspected_or_known_mronj", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("procedure_date", sa.Date(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("procedure_bleeding_risk", sa.String(length=48), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("procedure_osseous_risk", sa.String(length=48), nullable=False, server_default="UNKNOWN"),
    )
    op.add_column("patient_clinical_contexts", sa.Column("procedure_is_implant", sa.Boolean(), nullable=True))
    op.add_column("patient_clinical_contexts", sa.Column("ie_procedure_qualifies", sa.Boolean(), nullable=True))
    op.add_column("patient_clinical_contexts", sa.Column("oral_route_possible", sa.Boolean(), nullable=True))
    op.add_column(
        "patient_clinical_contexts",
        sa.Column("currently_taking_penicillin_or_amoxicillin", sa.Boolean(), nullable=True),
    )


def downgrade():
    op.drop_column("patient_clinical_contexts", "currently_taking_penicillin_or_amoxicillin")
    op.drop_column("patient_clinical_contexts", "oral_route_possible")
    op.drop_column("patient_clinical_contexts", "ie_procedure_qualifies")
    op.drop_column("patient_clinical_contexts", "procedure_is_implant")
    op.drop_column("patient_clinical_contexts", "procedure_osseous_risk")
    op.drop_column("patient_clinical_contexts", "procedure_bleeding_risk")
    op.drop_column("patient_clinical_contexts", "procedure_date")
    op.drop_column("patient_clinical_contexts", "suspected_or_known_mronj")
    op.drop_column("patient_clinical_contexts", "active_oral_infection_or_inflammation")
    op.drop_column("patient_clinical_contexts", "mronj_concurrent_risk_therapy")
    op.drop_column("patient_clinical_contexts", "mronj_duration_months")
    op.drop_column("patient_clinical_contexts", "mronj_route")
    op.drop_column("patient_clinical_contexts", "mronj_indication")
    op.drop_column("patient_clinical_contexts", "mronj_agent_class")
    op.drop_column("patient_clinical_contexts", "mronj_agents")
    op.drop_column("patient_clinical_contexts", "mronj_medication_status")
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
