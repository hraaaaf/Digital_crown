"""add Patient Companion opaque appointment references

Revision ID: pc020000010
Revises: pcrt0000009
"""

from alembic import op
import sqlalchemy as sa

revision = "pc020000010"
down_revision = "pcrt0000009"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_companion_appointment_refs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employer_id", "appointment_id", name="uq_pc_appointment_ref_tenant_appointment"),
    )
    op.create_index("ix_pc_appointment_ref_public_id", "patient_companion_appointment_refs", ["public_id"], unique=True)
    op.create_index("ix_pc_appointment_ref_employer_id", "patient_companion_appointment_refs", ["employer_id"], unique=False)
    op.create_index("ix_pc_appointment_ref_patient_id", "patient_companion_appointment_refs", ["patient_id"], unique=False)
    op.create_index("ix_pc_appointment_ref_appointment_id", "patient_companion_appointment_refs", ["appointment_id"], unique=False)
    op.create_index("ix_pc_appointment_ref_tenant_patient", "patient_companion_appointment_refs", ["employer_id", "patient_id"], unique=False)
    op.create_table(
        "patient_companion_agenda_slots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("practitioner_id", sa.Integer(), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("datetime_start", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["practitioner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resource_id"], ["agenda_resources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pc_agenda_slot_public_id", "patient_companion_agenda_slots", ["public_id"], unique=True)
    op.create_index("ix_pc_agenda_slot_employer_id", "patient_companion_agenda_slots", ["employer_id"], unique=False)
    op.create_index("ix_pc_agenda_slot_practitioner_id", "patient_companion_agenda_slots", ["practitioner_id"], unique=False)
    op.create_index("ix_pc_agenda_slot_resource_id", "patient_companion_agenda_slots", ["resource_id"], unique=False)
    op.create_index("ix_pc_agenda_slot_datetime_start", "patient_companion_agenda_slots", ["datetime_start"], unique=False)
    op.create_index("ix_pc_agenda_slot_expires_at", "patient_companion_agenda_slots", ["expires_at"], unique=False)
    op.create_index("ix_pc_agenda_slot_revoked_at", "patient_companion_agenda_slots", ["revoked_at"], unique=False)
    op.create_index("ix_pc_agenda_slot_consumed_at", "patient_companion_agenda_slots", ["consumed_at"], unique=False)
    op.create_index("ix_pc_agenda_slot_tenant_expiry", "patient_companion_agenda_slots", ["employer_id", "expires_at"], unique=False)
    op.create_table(
        "patient_companion_practitioner_refs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("practitioner_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["practitioner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employer_id", "practitioner_id", name="uq_pc_practitioner_ref_tenant_practitioner"),
    )
    op.create_index("ix_pc_practitioner_ref_public_id", "patient_companion_practitioner_refs", ["public_id"], unique=True)
    op.create_index("ix_pc_practitioner_ref_employer_id", "patient_companion_practitioner_refs", ["employer_id"], unique=False)
    op.create_index("ix_pc_practitioner_ref_practitioner_id", "patient_companion_practitioner_refs", ["practitioner_id"], unique=False)
    op.create_index("ix_pc_practitioner_ref_revoked_at", "patient_companion_practitioner_refs", ["revoked_at"], unique=False)


def downgrade():
    op.drop_index("ix_pc_practitioner_ref_revoked_at", table_name="patient_companion_practitioner_refs")
    op.drop_index("ix_pc_practitioner_ref_practitioner_id", table_name="patient_companion_practitioner_refs")
    op.drop_index("ix_pc_practitioner_ref_employer_id", table_name="patient_companion_practitioner_refs")
    op.drop_index("ix_pc_practitioner_ref_public_id", table_name="patient_companion_practitioner_refs")
    op.drop_table("patient_companion_practitioner_refs")
    op.drop_index("ix_pc_agenda_slot_tenant_expiry", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_consumed_at", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_revoked_at", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_expires_at", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_datetime_start", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_resource_id", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_practitioner_id", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_employer_id", table_name="patient_companion_agenda_slots")
    op.drop_index("ix_pc_agenda_slot_public_id", table_name="patient_companion_agenda_slots")
    op.drop_table("patient_companion_agenda_slots")
    op.drop_index("ix_pc_appointment_ref_tenant_patient", table_name="patient_companion_appointment_refs")
    op.drop_index("ix_pc_appointment_ref_appointment_id", table_name="patient_companion_appointment_refs")
    op.drop_index("ix_pc_appointment_ref_patient_id", table_name="patient_companion_appointment_refs")
    op.drop_index("ix_pc_appointment_ref_employer_id", table_name="patient_companion_appointment_refs")
    op.drop_index("ix_pc_appointment_ref_public_id", table_name="patient_companion_appointment_refs")
    op.drop_table("patient_companion_appointment_refs")
