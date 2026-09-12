"""add appointment practitioner

Revision ID: d3a55e700003
Revises: c2a55e700002
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa


revision = "d3a55e700003"
down_revision = "c2a55e700002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.add_column(sa.Column("praticien_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_appointments_praticien_id_users",
            "users",
            ["praticien_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_appointments_praticien_id", ["praticien_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("appointments") as batch_op:
        batch_op.drop_index("ix_appointments_praticien_id")
        batch_op.drop_constraint("fk_appointments_praticien_id_users", type_="foreignkey")
        batch_op.drop_column("praticien_id")
