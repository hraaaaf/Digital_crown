"""Add Ortho Journey F1A persistence.

Revision ID: ojf1a000006
Revises: a5th0000005
"""

from alembic import op
import sqlalchemy as sa


revision = "ojf1a000006"
down_revision = "a5th0000005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ortho_cases",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=20), nullable=False),
        sa.Column("current_phase_key", sa.String(length=32), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ortho_cases_id", "ortho_cases", ["id"], unique=False)
    op.create_index("ix_ortho_cases_employer_id", "ortho_cases", ["employer_id"], unique=False)
    op.create_index("ix_ortho_cases_patient_id", "ortho_cases", ["patient_id"], unique=False)
    op.create_index("ix_ortho_cases_lifecycle_status", "ortho_cases", ["lifecycle_status"], unique=False)
    op.create_index(
        "ix_ortho_cases_employer_patient_status",
        "ortho_cases",
        ["employer_id", "patient_id", "lifecycle_status"],
        unique=False,
    )

    op.create_table(
        "ortho_phase_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ortho_case_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("phase_key", sa.String(length=32), nullable=True),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ortho_case_id"], ["ortho_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ortho_phase_events_id", "ortho_phase_events", ["id"], unique=False)
    op.create_index("ix_ortho_phase_events_ortho_case_id", "ortho_phase_events", ["ortho_case_id"], unique=False)
    op.create_index("ix_ortho_phase_events_employer_id", "ortho_phase_events", ["employer_id"], unique=False)
    op.create_index("ix_ortho_phase_events_patient_id", "ortho_phase_events", ["patient_id"], unique=False)
    op.create_index("ix_ortho_phase_events_event_type", "ortho_phase_events", ["event_type"], unique=False)
    op.create_index("ix_ortho_phase_events_effective_at", "ortho_phase_events", ["effective_at"], unique=False)
    op.create_index(
        "ix_ortho_phase_events_employer_patient_effective",
        "ortho_phase_events",
        ["employer_id", "patient_id", "effective_at"],
        unique=False,
    )
    op.create_index(
        "ix_ortho_phase_events_case_effective",
        "ortho_phase_events",
        ["ortho_case_id", "effective_at"],
        unique=False,
    )


def downgrade():
    op.drop_table("ortho_phase_events")
    op.drop_table("ortho_cases")
