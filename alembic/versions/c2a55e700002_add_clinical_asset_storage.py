"""add clinical asset encrypted storage binding

Revision ID: c2a55e700002
Revises: c1a55e700001
Create Date: 2026-09-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2a55e700002"
down_revision: Union[str, None] = "c1a55e700001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clinical_assets", sa.Column("storage_key", sa.String(length=512), nullable=True))
    op.add_column("clinical_assets", sa.Column("storage_format", sa.String(length=32), nullable=True))
    op.add_column("clinical_assets", sa.Column("stored_at", sa.DateTime(), nullable=True))

    op.create_index("ix_clinical_assets_storage_key", "clinical_assets", ["storage_key"], unique=False)
    op.create_index("ix_clinical_assets_stored_at", "clinical_assets", ["stored_at"], unique=False)
    op.create_index(
        "ix_clinical_assets_tenant_sha256",
        "clinical_assets",
        ["employer_id", "sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_assets_tenant_sha256", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_stored_at", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_storage_key", table_name="clinical_assets")
    op.drop_column("clinical_assets", "stored_at")
    op.drop_column("clinical_assets", "storage_format")
    op.drop_column("clinical_assets", "storage_key")
