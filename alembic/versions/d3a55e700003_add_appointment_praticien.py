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
    op.add_column(
        "appointments",
        sa.Column("praticien_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_appointments_praticien_id_users",
        "appointments",
        "users",
        ["praticien_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_appointments_praticien_id",
        "appointments",
        ["praticien_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_appointments_praticien_id", table_name="appointments")
    op.drop_constraint(
        "fk_appointments_praticien_id_users",
        "appointments",
        type_="foreignkey",
    )
    op.drop_column("appointments", "praticien_id")
