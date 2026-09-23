"""PC-08 secure messaging canonical message table.

Revision ID: pc080000015
Revises: pc070000014
"""

from alembic import op
import sqlalchemy as sa

revision = "pc080000015"
down_revision = "pc070000014"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_companion_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("access_id", sa.Integer(), sa.ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_message_id", sa.String(length=36), nullable=False),
        sa.Column("sender_kind", sa.String(length=16), nullable=False),
        sa.Column("sender_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("staff_read_at", sa.DateTime(), nullable=True),
        sa.Column("staff_read_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("patient_received_at", sa.DateTime(), nullable=True),
        sa.Column("patient_read_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("access_id", "client_message_id", name="uq_pc08_message_access_client"),
    )
    op.create_index("ix_pc08_message_access_created", "patient_companion_messages", ["access_id", "created_at"])
    op.create_index("ix_pc08_message_tenant_patient_access", "patient_companion_messages", ["employer_id", "patient_id", "access_id"])
    op.create_index("ix_patient_companion_messages_public_id", "patient_companion_messages", ["public_id"], unique=True)
    op.create_index("ix_patient_companion_messages_access_id", "patient_companion_messages", ["access_id"])
    op.create_index("ix_patient_companion_messages_employer_id", "patient_companion_messages", ["employer_id"])
    op.create_index("ix_patient_companion_messages_patient_id", "patient_companion_messages", ["patient_id"])


def downgrade():
    op.drop_table("patient_companion_messages")
