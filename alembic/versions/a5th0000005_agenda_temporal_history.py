"""Agenda A5 temporal/history hardening.

Revision ID: a5th0000005
Revises: a4rs0000004
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a5th0000005"
down_revision: Union[str, None] = "a4rs0000004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.add_column("appointments", sa.Column("deleted_by", sa.Integer(), nullable=True))
    op.create_foreign_key("fk_appointments_deleted_by_users", "appointments", "users", ["deleted_by"], ["id"], ondelete="SET NULL")
    op.create_index("ix_appointments_deleted_at", "appointments", ["deleted_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_appointments_deleted_at", table_name="appointments")
    op.drop_constraint("fk_appointments_deleted_by_users", "appointments", type_="foreignkey")
    op.drop_column("appointments", "deleted_by")
    op.drop_column("appointments", "deleted_at")
