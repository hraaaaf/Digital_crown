"""add agenda physical resources

Revision ID: a4rs0000004
Revises: a3pa0000003
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a4rs0000004"
down_revision: Union[str, None] = "a3pa0000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agenda_resources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=20), nullable=False, server_default="CHAIR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employer_id", "name", name="uq_agenda_resources_tenant_name"),
    )
    op.create_index("ix_agenda_resources_tenant_active", "agenda_resources", ["employer_id", "is_active"], unique=False)
    op.add_column("appointments", sa.Column("resource_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_appointments_resource_id_agenda_resources",
        "appointments", "agenda_resources", ["resource_id"], ["id"], ondelete="SET NULL",
    )
    op.create_index("ix_appointments_resource_id", "appointments", ["resource_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_appointments_resource_id", table_name="appointments")
    op.drop_constraint("fk_appointments_resource_id_agenda_resources", "appointments", type_="foreignkey")
    op.drop_column("appointments", "resource_id")
    op.drop_index("ix_agenda_resources_tenant_active", table_name="agenda_resources")
    op.drop_table("agenda_resources")
