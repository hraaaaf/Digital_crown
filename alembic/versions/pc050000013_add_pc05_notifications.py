"""PC-05 Patient Companion notification receipts and preferences.

Revision ID: pc050000013
Revises: pc040000012
"""

from alembic import op
import sqlalchemy as sa


revision = "pc050000013"
down_revision = "pc040000012"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "patient_companion_accesses",
        sa.Column("notification_preferences_json", sa.Text(), nullable=True),
    )
    op.create_table(
        "patient_companion_notification_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("access_id", sa.Integer(), sa.ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_key", sa.String(length=180), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("snoozed_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("access_id", "source_key", name="uq_pc_notification_receipt_access_source"),
    )
    op.create_index("ix_pc_notification_receipt_access_id", "patient_companion_notification_receipts", ["access_id"])
    op.create_index("ix_pc_notification_receipt_tenant_patient", "patient_companion_notification_receipts", ["employer_id", "patient_id"])
    op.create_index("ix_pc_notification_receipt_read_at", "patient_companion_notification_receipts", ["read_at"])
    op.create_index("ix_pc_notification_receipt_snoozed_until", "patient_companion_notification_receipts", ["snoozed_until"])


def downgrade():
    op.drop_table("patient_companion_notification_receipts")
    op.drop_column("patient_companion_accesses", "notification_preferences_json")
