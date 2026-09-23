"""PC-09 teleconsultation session and signaling tables.

Revision ID: pc090000016
Revises: pc080000015
"""

from alembic import op
import sqlalchemy as sa

revision = "pc090000016"
down_revision = "pc080000015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_companion_teleconsult_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("access_id", sa.Integer(), sa.ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("appointment_ref_id", sa.Integer(), sa.ForeignKey("patient_companion_appointment_refs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("patient_joined_at", sa.DateTime(), nullable=True),
        sa.Column("staff_joined_at", sa.DateTime(), nullable=True),
        sa.Column("patient_connected_at", sa.DateTime(), nullable=True),
        sa.Column("staff_connected_at", sa.DateTime(), nullable=True),
        sa.Column("connected_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("ended_by", sa.String(length=16), nullable=True),
        sa.Column("failure_code", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_patient_companion_teleconsult_sessions_public_id", "patient_companion_teleconsult_sessions", ["public_id"], unique=True)
    op.create_index("ix_patient_companion_teleconsult_sessions_access_id", "patient_companion_teleconsult_sessions", ["access_id"])
    op.create_index("ix_patient_companion_teleconsult_sessions_employer_id", "patient_companion_teleconsult_sessions", ["employer_id"])
    op.create_index("ix_patient_companion_teleconsult_sessions_patient_id", "patient_companion_teleconsult_sessions", ["patient_id"])
    op.create_index("ix_patient_companion_teleconsult_sessions_appointment_ref_id", "patient_companion_teleconsult_sessions", ["appointment_ref_id"])
    op.create_index("ix_patient_companion_teleconsult_sessions_created_by_user_id", "patient_companion_teleconsult_sessions", ["created_by_user_id"])
    op.create_index("ix_patient_companion_teleconsult_sessions_state", "patient_companion_teleconsult_sessions", ["state"])
    op.create_index("ix_patient_companion_teleconsult_sessions_expires_at", "patient_companion_teleconsult_sessions", ["expires_at"])
    op.create_index("ix_pc09_session_access_state", "patient_companion_teleconsult_sessions", ["access_id", "state"])
    op.create_index("ix_pc09_session_tenant_patient_state", "patient_companion_teleconsult_sessions", ["employer_id", "patient_id", "state"])

    op.create_table(
        "patient_companion_teleconsult_signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("patient_companion_teleconsult_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_signal_id", sa.String(length=36), nullable=False),
        sa.Column("sender_kind", sa.String(length=16), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signal_type", sa.String(length=16), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("session_id", "client_signal_id", name="uq_pc09_signal_session_client"),
    )
    op.create_index("ix_patient_companion_teleconsult_signals_public_id", "patient_companion_teleconsult_signals", ["public_id"], unique=True)
    op.create_index("ix_patient_companion_teleconsult_signals_session_id", "patient_companion_teleconsult_signals", ["session_id"])
    op.create_index("ix_pc09_signal_session_id_order", "patient_companion_teleconsult_signals", ["session_id", "id"])


def downgrade():
    op.drop_table("patient_companion_teleconsult_signals")
    op.drop_table("patient_companion_teleconsult_sessions")
