"""add patient companion authorization tables

Revision ID: d0b000000001
Revises: c2ie0000002
Create Date: 2026-09-15

The companion tables were previously created as a side effect of application
startup metadata registration. They are now part of the explicit schema contract.
The upgrade is tolerant of a table/index already created by an older isolated
bootstrap, but never changes or backfills existing rows.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d0b000000001"
down_revision: Union[str, None] = "c2ie0000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_tables(bind) -> set[str]:
    return set(sa.inspect(bind).get_table_names())


def _create_index_if_missing(bind, name: str, table: str, columns: list[str], *, unique: bool = False) -> None:
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes(table)}
    if name not in indexes:
        op.create_index(name, table, columns, unique=unique)


def _create_companion_table(bind, name: str, *elements) -> None:
    if name not in _existing_tables(bind):
        op.create_table(name, *elements)


def upgrade() -> None:
    bind = op.get_bind()

    _create_companion_table(
        bind,
        "patient_companion_identities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("subject", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "provider",
            "subject",
            name="uq_patient_companion_identity_provider_subject",
        ),
    )
    _create_index_if_missing(bind, "ix_patient_companion_identities_id", "patient_companion_identities", ["id"])
    _create_index_if_missing(bind, "ix_patient_companion_identities_revoked_at", "patient_companion_identities", ["revoked_at"])

    _create_companion_table(
        bind,
        "patient_companion_accesses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("identity_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=24), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["identity_id"], ["patient_companion_identities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "identity_id",
            "employer_id",
            "patient_id",
            name="uq_patient_companion_access_identity_tenant_patient",
        ),
    )
    _create_index_if_missing(bind, "ix_patient_companion_accesses_id", "patient_companion_accesses", ["id"])
    _create_index_if_missing(bind, "ix_patient_companion_accesses_public_id", "patient_companion_accesses", ["public_id"], unique=True)
    _create_index_if_missing(bind, "ix_patient_companion_accesses_identity_id", "patient_companion_accesses", ["identity_id"])
    _create_index_if_missing(bind, "ix_patient_companion_accesses_employer_id", "patient_companion_accesses", ["employer_id"])
    _create_index_if_missing(bind, "ix_patient_companion_accesses_patient_id", "patient_companion_accesses", ["patient_id"])
    _create_index_if_missing(bind, "ix_patient_companion_accesses_revoked_at", "patient_companion_accesses", ["revoked_at"])
    _create_index_if_missing(bind, "ix_patient_companion_access_tenant_patient", "patient_companion_accesses", ["employer_id", "patient_id"])

    _create_companion_table(
        bind,
        "patient_companion_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("manual_code_hash", sa.String(length=64), nullable=False),
        sa.Column("recipient_type", sa.String(length=16), nullable=False),
        sa.Column("recipient_hash", sa.String(length=64), nullable=False),
        sa.Column("relationship_type", sa.String(length=24), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("consumed_by_identity_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["consumed_by_identity_id"],
            ["patient_companion_identities.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index_if_missing(bind, "ix_patient_companion_invitations_id", "patient_companion_invitations", ["id"])
    _create_index_if_missing(bind, "ix_patient_companion_invitations_public_id", "patient_companion_invitations", ["public_id"], unique=True)
    _create_index_if_missing(bind, "ix_patient_companion_invitations_employer_id", "patient_companion_invitations", ["employer_id"])
    _create_index_if_missing(bind, "ix_patient_companion_invitations_patient_id", "patient_companion_invitations", ["patient_id"])
    _create_index_if_missing(bind, "ix_patient_companion_invitations_token_hash", "patient_companion_invitations", ["token_hash"], unique=True)
    _create_index_if_missing(bind, "ix_patient_companion_invitations_manual_code_hash", "patient_companion_invitations", ["manual_code_hash"], unique=True)
    _create_index_if_missing(bind, "ix_patient_companion_invitations_recipient_hash", "patient_companion_invitations", ["recipient_hash"])
    _create_index_if_missing(bind, "ix_patient_companion_invitations_expires_at", "patient_companion_invitations", ["expires_at"])
    _create_index_if_missing(bind, "ix_patient_companion_invitations_consumed_at", "patient_companion_invitations", ["consumed_at"])
    _create_index_if_missing(bind, "ix_patient_companion_invitations_revoked_at", "patient_companion_invitations", ["revoked_at"])
    _create_index_if_missing(bind, "ix_patient_companion_invitation_tenant_patient", "patient_companion_invitations", ["employer_id", "patient_id"])

    _create_companion_table(
        bind,
        "patient_companion_share_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("resource_type", sa.String(length=32), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("granted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "employer_id",
            "patient_id",
            "resource_type",
            "resource_id",
            name="uq_patient_companion_share_resource",
        ),
    )
    _create_index_if_missing(bind, "ix_patient_companion_share_grants_id", "patient_companion_share_grants", ["id"])
    _create_index_if_missing(bind, "ix_patient_companion_share_grants_public_id", "patient_companion_share_grants", ["public_id"], unique=True)
    _create_index_if_missing(bind, "ix_patient_companion_share_grants_employer_id", "patient_companion_share_grants", ["employer_id"])
    _create_index_if_missing(bind, "ix_patient_companion_share_grants_patient_id", "patient_companion_share_grants", ["patient_id"])
    _create_index_if_missing(bind, "ix_patient_companion_share_grants_revoked_at", "patient_companion_share_grants", ["revoked_at"])
    _create_index_if_missing(bind, "ix_patient_companion_share_tenant_patient", "patient_companion_share_grants", ["employer_id", "patient_id"])


def downgrade() -> None:
    raise RuntimeError(
        "Destructive downgrade of Companion tables is intentionally refused; "
        "restore a reviewed database backup instead."
    )
