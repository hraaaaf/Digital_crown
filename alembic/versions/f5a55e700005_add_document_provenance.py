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
    # Batch mode keeps the same migration valid on cabinet SQLite and PostgreSQL.
    # SQLite cannot add named foreign keys in place after table creation.
    with op.batch_alter_table("document_archives") as batch_op:
        batch_op.add_column(sa.Column("author_practitioner_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("signed_by_practitioner_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("signed_at", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_document_archives_author_practitioner_id_users",
            "users",
            ["author_practitioner_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_document_archives_signed_by_practitioner_id_users",
            "users",
            ["signed_by_practitioner_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("document_archives") as batch_op:
        batch_op.drop_constraint(
            "fk_document_archives_signed_by_practitioner_id_users",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_document_archives_author_practitioner_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("signed_at")
        batch_op.drop_column("signed_by_practitioner_id")
        batch_op.drop_column("author_practitioner_id")
