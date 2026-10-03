"""V1.5-03.2 station identity and pairing.

Revision ID: neo000000026
Revises: neo000000025
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000026"
down_revision = "neo000000025"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("workstation_modes", sa.Column("display_name", sa.String(length=80), nullable=True))
    op.add_column("workstation_modes", sa.Column("revoked_at", sa.DateTime(), nullable=True))
    op.add_column("workstation_modes", sa.Column("last_seen_at", sa.DateTime(), nullable=True))
    op.create_index("ix_workstation_modes_revoked_at", "workstation_modes", ["revoked_at"])

    op.create_table(
        "workstation_pairing_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_workstation_pairing_codes_employer_id", "workstation_pairing_codes", ["employer_id"])
    op.create_index("ix_workstation_pairing_codes_code_hash", "workstation_pairing_codes", ["code_hash"], unique=True)
    op.create_index("ix_workstation_pairing_codes_expires_at", "workstation_pairing_codes", ["expires_at"])
    op.create_index(
        "uq_workstation_pairing_codes_one_active",
        "workstation_pairing_codes",
        ["employer_id"],
        unique=True,
        sqlite_where=sa.text("used_at IS NULL"),
        postgresql_where=sa.text("used_at IS NULL"),
    )


def downgrade():
    op.drop_index("uq_workstation_pairing_codes_one_active", table_name="workstation_pairing_codes")
    op.drop_index("ix_workstation_pairing_codes_expires_at", table_name="workstation_pairing_codes")
    op.drop_index("ix_workstation_pairing_codes_code_hash", table_name="workstation_pairing_codes")
    op.drop_index("ix_workstation_pairing_codes_employer_id", table_name="workstation_pairing_codes")
    op.drop_table("workstation_pairing_codes")
    op.drop_index("ix_workstation_modes_revoked_at", table_name="workstation_modes")
    op.drop_column("workstation_modes", "last_seen_at")
    op.drop_column("workstation_modes", "revoked_at")
    op.drop_column("workstation_modes", "display_name")
