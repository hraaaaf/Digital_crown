"""V1.5-03.3 station patient handoff session.

Revision ID: neo000000027
Revises: neo000000026
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000027"
down_revision = "neo000000026"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workstation_patient_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workstation_id", sa.String(length=36), sa.ForeignKey("workstation_modes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_token_hash", sa.String(length=64), nullable=False),
        sa.Column("patient_access_id", sa.Integer(), sa.ForeignKey("patient_companion_accesses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fallback_failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("purged_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_workstation_patient_sessions_employer_id", "workstation_patient_sessions", ["employer_id"])
    op.create_index("ix_workstation_patient_sessions_workstation_id", "workstation_patient_sessions", ["workstation_id"])
    op.create_index(
        "uq_workstation_patient_sessions_one_active",
        "workstation_patient_sessions",
        ["workstation_id"],
        unique=True,
        sqlite_where=sa.text("purged_at IS NULL"),
        postgresql_where=sa.text("purged_at IS NULL"),
    )
    op.create_index("ix_workstation_patient_sessions_claim_token_hash", "workstation_patient_sessions", ["claim_token_hash"], unique=True)
    op.create_index("ix_workstation_patient_sessions_patient_access_id", "workstation_patient_sessions", ["patient_access_id"])
    op.create_index("ix_workstation_patient_sessions_patient_id", "workstation_patient_sessions", ["patient_id"])
    op.create_index("ix_workstation_patient_sessions_expires_at", "workstation_patient_sessions", ["expires_at"])
    op.create_index("ix_workstation_patient_sessions_claimed_at", "workstation_patient_sessions", ["claimed_at"])
    op.create_index("ix_workstation_patient_sessions_purged_at", "workstation_patient_sessions", ["purged_at"])
    op.add_column(
        "cabinet_configs",
        sa.Column("station_identification_fallback", sa.String(length=24), nullable=False, server_default="disabled"),
    )


def downgrade():
    op.drop_column("cabinet_configs", "station_identification_fallback")
    op.drop_table("workstation_patient_sessions")
