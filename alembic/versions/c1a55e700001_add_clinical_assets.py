"""add clinical asset metadata registry

Revision ID: c1a55e700001
Revises: f7a8b9c0d1e2
Create Date: 2026-09-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a55e700001"
down_revision: Union[str, None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinical_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("asset_type", sa.String(length=32), nullable=False),
        sa.Column("source_kind", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.String(length=255), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("mime_type", sa.String(length=127), nullable=True),
        sa.Column("byte_size", sa.BigInteger(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("timepoint", sa.String(length=32), nullable=True),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("parent_asset_id", sa.Integer(), nullable=True),
        sa.Column("provenance_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "asset_type IN ('PHOTO','RADIOGRAPH','DOCUMENT','VIDEO','AUDIO','OTHER')",
            name="ck_clinical_assets_asset_type",
        ),
        sa.CheckConstraint(
            "source_kind IN ('UPLOAD','IMPORT','DERIVED','CLINICAL_ANALYSIS','DEVICE_CAPTURE')",
            name="ck_clinical_assets_source_kind",
        ),
        sa.CheckConstraint(
            "byte_size IS NULL OR byte_size >= 0",
            name="ck_clinical_assets_byte_size_nonnegative",
        ),
        sa.CheckConstraint(
            "sha256 IS NULL OR length(sha256) = 64",
            name="ck_clinical_assets_sha256_length",
        ),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["parent_asset_id"], ["clinical_assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_clinical_assets_id", "clinical_assets", ["id"], unique=False)
    op.create_index("ix_clinical_assets_employer_id", "clinical_assets", ["employer_id"], unique=False)
    op.create_index("ix_clinical_assets_patient_id", "clinical_assets", ["patient_id"], unique=False)
    op.create_index("ix_clinical_assets_asset_type", "clinical_assets", ["asset_type"], unique=False)
    op.create_index("ix_clinical_assets_source_kind", "clinical_assets", ["source_kind"], unique=False)
    op.create_index("ix_clinical_assets_source_ref", "clinical_assets", ["source_ref"], unique=False)
    op.create_index("ix_clinical_assets_sha256", "clinical_assets", ["sha256"], unique=False)
    op.create_index("ix_clinical_assets_timepoint", "clinical_assets", ["timepoint"], unique=False)
    op.create_index("ix_clinical_assets_captured_at", "clinical_assets", ["captured_at"], unique=False)
    op.create_index("ix_clinical_assets_created_by", "clinical_assets", ["created_by"], unique=False)
    op.create_index("ix_clinical_assets_parent_asset_id", "clinical_assets", ["parent_asset_id"], unique=False)
    op.create_index("ix_clinical_assets_created_at", "clinical_assets", ["created_at"], unique=False)
    op.create_index(
        "ix_clinical_assets_tenant_patient_created",
        "clinical_assets",
        ["employer_id", "patient_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_clinical_assets_tenant_patient_created", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_created_at", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_parent_asset_id", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_created_by", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_captured_at", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_timepoint", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_sha256", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_source_ref", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_source_kind", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_asset_type", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_patient_id", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_employer_id", table_name="clinical_assets")
    op.drop_index("ix_clinical_assets_id", table_name="clinical_assets")
    op.drop_table("clinical_assets")
