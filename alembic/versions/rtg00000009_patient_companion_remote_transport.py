"""Patient Companion remote E2E key registry and replay ledger.

Revision ID: rtg00000009
Revises: ojf20000008
Create Date: 2026-09-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "rtg00000009"
down_revision: Union[str, None] = "ojf20000008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_companion_remote_key_sets",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("access_id", sa.Integer(), nullable=False),
        sa.Column("signing_kid", sa.String(length=36), nullable=False),
        sa.Column("signing_public_jwk", sa.Text(), nullable=False),
        sa.Column("encryption_kid", sa.String(length=36), nullable=False),
        sa.Column("encryption_public_jwk", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["access_id"],
            ["patient_companion_accesses.id"],
            name="fk_pc_remote_keys_access",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("public_id", name="uq_pc_remote_keys_public_id"),
        sa.UniqueConstraint("access_id", "signing_kid", name="uq_pc_remote_keys_access_signing_kid"),
        sa.UniqueConstraint("access_id", "encryption_kid", name="uq_pc_remote_keys_access_encryption_kid"),
    )
    op.create_index(
        "ix_pc_remote_key_sets_public_id",
        "patient_companion_remote_key_sets",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_pc_remote_key_sets_access_id",
        "patient_companion_remote_key_sets",
        ["access_id"],
        unique=False,
    )
    op.create_index(
        "ix_pc_remote_key_sets_state",
        "patient_companion_remote_key_sets",
        ["state"],
        unique=False,
    )
    op.create_index(
        "ix_pc_remote_key_sets_revoked_at",
        "patient_companion_remote_key_sets",
        ["revoked_at"],
        unique=False,
    )
    op.create_index(
        "uq_pc_remote_keys_one_active_per_access",
        "patient_companion_remote_key_sets",
        ["access_id"],
        unique=True,
        sqlite_where=sa.text("state = 'ACTIVE'"),
        postgresql_where=sa.text("state = 'ACTIVE'"),
    )

    op.create_table(
        "patient_companion_remote_message_receipts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("access_id", sa.Integer(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=36), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("result_digest", sa.String(length=64), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["access_id"],
            ["patient_companion_accesses.id"],
            name="fk_pc_remote_receipt_access",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("message_id", name="uq_pc_remote_message_id"),
        sa.UniqueConstraint("access_id", "idempotency_key", name="uq_pc_remote_idempotency"),
    )
    op.create_index(
        "ix_pc_remote_message_receipts_access_id",
        "patient_companion_remote_message_receipts",
        ["access_id"],
        unique=False,
    )
    op.create_index(
        "ix_pc_remote_receipt_access_received",
        "patient_companion_remote_message_receipts",
        ["access_id", "received_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pc_remote_receipt_access_received", table_name="patient_companion_remote_message_receipts")
    op.drop_index("ix_pc_remote_message_receipts_access_id", table_name="patient_companion_remote_message_receipts")
    op.drop_table("patient_companion_remote_message_receipts")

    op.drop_index("uq_pc_remote_keys_one_active_per_access", table_name="patient_companion_remote_key_sets")
    op.drop_index("ix_pc_remote_key_sets_revoked_at", table_name="patient_companion_remote_key_sets")
    op.drop_index("ix_pc_remote_key_sets_state", table_name="patient_companion_remote_key_sets")
    op.drop_index("ix_pc_remote_key_sets_access_id", table_name="patient_companion_remote_key_sets")
    op.drop_index("ix_pc_remote_key_sets_public_id", table_name="patient_companion_remote_key_sets")
    op.drop_table("patient_companion_remote_key_sets")
