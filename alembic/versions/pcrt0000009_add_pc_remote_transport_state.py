"""add Patient Companion remote transport keysets and replay ledger

Revision ID: pcrt0000009
Revises: ojf20000008
Create Date: 2026-09-19
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "pcrt0000009"
down_revision: Union[str, None] = "ojf20000008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patient_companion_cabinet_remote_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("kid", sa.String(length=36), nullable=False),
        sa.Column("key_use", sa.String(length=8), nullable=False),
        sa.Column("public_jwk_json", sa.Text(), nullable=False),
        sa.Column("protected_private_jwk_b64", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kid"),
    )
    op.create_index(
        "ix_pc_cabinet_remote_key_tenant_use_status",
        "patient_companion_cabinet_remote_keys",
        ["employer_id", "key_use", "status"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_cabinet_remote_keys_employer_id",
        "patient_companion_cabinet_remote_keys",
        ["employer_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_cabinet_remote_keys_kid",
        "patient_companion_cabinet_remote_keys",
        ["kid"],
        unique=True,
    )
    op.create_index(
        "ix_patient_companion_cabinet_remote_keys_status",
        "patient_companion_cabinet_remote_keys",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_cabinet_remote_keys_revoked_at",
        "patient_companion_cabinet_remote_keys",
        ["revoked_at"],
        unique=False,
    )

    op.create_table(
        "patient_companion_remote_keysets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("access_id", sa.Integer(), nullable=False),
        sa.Column("patient_signing_kid", sa.String(length=36), nullable=False),
        sa.Column("patient_signing_public_jwk_json", sa.Text(), nullable=False),
        sa.Column("patient_encryption_kid", sa.String(length=36), nullable=False),
        sa.Column("patient_encryption_public_jwk_json", sa.Text(), nullable=False),
        sa.Column("cabinet_signing_kid", sa.String(length=36), nullable=False),
        sa.Column("cabinet_encryption_kid", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["access_id"], ["patient_companion_accesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
    )
    op.create_index(
        "ix_pc_remote_keyset_access_status",
        "patient_companion_remote_keysets",
        ["access_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_remote_keysets_access_id",
        "patient_companion_remote_keysets",
        ["access_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_remote_keysets_public_id",
        "patient_companion_remote_keysets",
        ["public_id"],
        unique=True,
    )
    op.create_index(
        "ix_patient_companion_remote_keysets_status",
        "patient_companion_remote_keysets",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_remote_keysets_revoked_at",
        "patient_companion_remote_keysets",
        ["revoked_at"],
        unique=False,
    )

    op.create_table(
        "patient_companion_remote_receipts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("access_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=36), nullable=False),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="PROCESSING"),
        sa.Column("response_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["access_id"], ["patient_companion_accesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("access_id", "message_id", name="uq_pc_remote_receipt_access_message"),
        sa.UniqueConstraint("access_id", "idempotency_key", name="uq_pc_remote_receipt_access_idempotency"),
    )
    op.create_index(
        "ix_pc_remote_receipt_access_status",
        "patient_companion_remote_receipts",
        ["access_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_remote_receipts_access_id",
        "patient_companion_remote_receipts",
        ["access_id"],
        unique=False,
    )
    op.create_index(
        "ix_patient_companion_remote_receipts_status",
        "patient_companion_remote_receipts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_patient_companion_remote_receipts_status", table_name="patient_companion_remote_receipts")
    op.drop_index("ix_patient_companion_remote_receipts_access_id", table_name="patient_companion_remote_receipts")
    op.drop_index("ix_pc_remote_receipt_access_status", table_name="patient_companion_remote_receipts")
    op.drop_table("patient_companion_remote_receipts")

    op.drop_index("ix_patient_companion_remote_keysets_revoked_at", table_name="patient_companion_remote_keysets")
    op.drop_index("ix_patient_companion_remote_keysets_status", table_name="patient_companion_remote_keysets")
    op.drop_index("ix_patient_companion_remote_keysets_public_id", table_name="patient_companion_remote_keysets")
    op.drop_index("ix_patient_companion_remote_keysets_access_id", table_name="patient_companion_remote_keysets")
    op.drop_index("ix_pc_remote_keyset_access_status", table_name="patient_companion_remote_keysets")
    op.drop_table("patient_companion_remote_keysets")

    op.drop_index("ix_patient_companion_cabinet_remote_keys_revoked_at", table_name="patient_companion_cabinet_remote_keys")
    op.drop_index("ix_patient_companion_cabinet_remote_keys_status", table_name="patient_companion_cabinet_remote_keys")
    op.drop_index("ix_patient_companion_cabinet_remote_keys_kid", table_name="patient_companion_cabinet_remote_keys")
    op.drop_index("ix_patient_companion_cabinet_remote_keys_employer_id", table_name="patient_companion_cabinet_remote_keys")
    op.drop_index("ix_pc_cabinet_remote_key_tenant_use_status", table_name="patient_companion_cabinet_remote_keys")
    op.drop_table("patient_companion_cabinet_remote_keys")
