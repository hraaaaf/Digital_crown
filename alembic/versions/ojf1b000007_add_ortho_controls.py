"""Add Ortho Journey F1B structured controls.

Revision ID: ojf1b000007
Revises: ojf1a000006
"""

from alembic import op
import sqlalchemy as sa


revision = "ojf1b000007"
down_revision = "ojf1a000006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ortho_controls",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ortho_case_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("phase_key", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("next_control_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "phase_key IS NULL OR phase_key IN ('DIAGNOSTIC','PREPARATION','APPAREILLAGE','ALIGNEMENT','FINITION','CONTENTION','CLOTURE')",
            name="ck_ortho_controls_phase_key",
        ),
        sa.CheckConstraint(
            "next_control_at IS NULL OR next_control_at >= occurred_at",
            name="ck_ortho_controls_next_after_control",
        ),
        sa.ForeignKeyConstraint(["ortho_case_id"], ["ortho_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ortho_controls_id", "ortho_controls", ["id"], unique=False)
    op.create_index("ix_ortho_controls_ortho_case_id", "ortho_controls", ["ortho_case_id"], unique=False)
    op.create_index("ix_ortho_controls_employer_id", "ortho_controls", ["employer_id"], unique=False)
    op.create_index("ix_ortho_controls_patient_id", "ortho_controls", ["patient_id"], unique=False)
    op.create_index("ix_ortho_controls_appointment_id", "ortho_controls", ["appointment_id"], unique=False)
    op.create_index("ix_ortho_controls_occurred_at", "ortho_controls", ["occurred_at"], unique=False)
    op.create_index(
        "ix_ortho_controls_employer_patient_occurred",
        "ortho_controls",
        ["employer_id", "patient_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_ortho_controls_case_occurred",
        "ortho_controls",
        ["ortho_case_id", "occurred_at"],
        unique=False,
    )


def downgrade():
    op.drop_table("ortho_controls")
