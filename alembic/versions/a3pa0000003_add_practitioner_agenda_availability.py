"""add practitioner agenda availability

Revision ID: a3pa0000003
Revises: c2ie0000002
Create Date: 2026-09-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3pa0000003"
down_revision: Union[str, None] = "c2ie0000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "practitioner_agenda_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("practitioner_id", sa.Integer(), nullable=False),
        sa.Column("weekly_schedule_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["practitioner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employer_id",
            "practitioner_id",
            name="uq_practitioner_agenda_settings_tenant_practitioner",
        ),
    )
    op.create_index(
        "ix_practitioner_agenda_settings_tenant_practitioner",
        "practitioner_agenda_settings",
        ["employer_id", "practitioner_id"],
        unique=False,
    )

    op.create_table(
        "practitioner_agenda_exceptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("practitioner_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["practitioner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_practitioner_agenda_exceptions_tenant_practitioner_dates",
        "practitioner_agenda_exceptions",
        ["employer_id", "practitioner_id", "start_date", "end_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_practitioner_agenda_exceptions_tenant_practitioner_dates",
        table_name="practitioner_agenda_exceptions",
    )
    op.drop_table("practitioner_agenda_exceptions")
    op.drop_index(
        "ix_practitioner_agenda_settings_tenant_practitioner",
        table_name="practitioner_agenda_settings",
    )
    op.drop_table("practitioner_agenda_settings")
