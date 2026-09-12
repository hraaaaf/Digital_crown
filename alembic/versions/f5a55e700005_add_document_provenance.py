"""add document author and signature provenance

Revision ID: f5a55e700005
Revises: e4a55e700004
Create Date: 2026-09-12

Additive-only P3 migration. Existing archives remain untouched: NULL means the
historical author/signature was not recorded and must not be inferred.
"""
from alembic import op
import sqlalchemy as sa


revision = "f5a55e700005"
down_revision = "e4a55e700004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_archives",
        sa.Column("author_practitioner_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_archives",
        sa.Column("signed_by_practitioner_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "document_archives",
        sa.Column("signed_at", sa.DateTime(), nullable=True),
    )
    op.create_foreign_key(
        "fk_document_archives_author_practitioner_id_users",
        "document_archives",
        "users",
        ["author_practitioner_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_document_archives_signed_by_practitioner_id_users",
        "document_archives",
        "users",
        ["signed_by_practitioner_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_document_archives_signed_by_practitioner_id_users",
        "document_archives",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_document_archives_author_practitioner_id_users",
        "document_archives",
        type_="foreignkey",
    )
    op.drop_column("document_archives", "signed_at")
    op.drop_column("document_archives", "signed_by_practitioner_id")
    op.drop_column("document_archives", "author_practitioner_id")
