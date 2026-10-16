"""Persist a DB-owned appointment revision and safe overlap expression index.

Revision ID: neo000000032
Revises: neo000000031
"""
from alembic import op
import sqlalchemy as sa

from backend.core.appointment_revision_ddl import (
    install_appointment_overlap_index,
    install_appointment_revision_guard,
    remove_appointment_overlap_index,
    remove_appointment_revision_guard,
)

revision = "neo000000032"
down_revision = "neo000000031"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "appointments",
        sa.Column(
            "clinical_revision", sa.Integer(), nullable=False,
            server_default=sa.text("0"),
        ),
    )
    bind = op.get_bind()
    install_appointment_revision_guard(bind)
    install_appointment_overlap_index(bind)


def downgrade():
    bind = op.get_bind()
    remove_appointment_overlap_index(bind)
    remove_appointment_revision_guard(bind)
    op.drop_column("appointments", "clinical_revision")
