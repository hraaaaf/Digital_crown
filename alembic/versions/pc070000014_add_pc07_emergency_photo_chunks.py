"""PC-07 emergency photo chunk assembly.

Revision ID: pc070000014
Revises: pc050000013
"""

from alembic import op
import sqlalchemy as sa

revision = "pc070000014"
down_revision = "pc050000013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_companion_emergency_photo_uploads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("access_id", sa.Integer(), sa.ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("object_sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="UPLOADING"),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("clinical_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("access_id", "public_id", name="uq_pc07_photo_upload_access_public"),
    )
    op.create_index("ix_pc07_photo_upload_access_status", "patient_companion_emergency_photo_uploads", ["access_id", "status"])
    op.create_index("ix_pc07_photo_upload_expires_at", "patient_companion_emergency_photo_uploads", ["expires_at"])
    op.create_index("ix_patient_companion_emergency_photo_uploads_public_id", "patient_companion_emergency_photo_uploads", ["public_id"])
    op.create_index("ix_patient_companion_emergency_photo_uploads_access_id", "patient_companion_emergency_photo_uploads", ["access_id"])
    op.create_index("ix_patient_companion_emergency_photo_uploads_employer_id", "patient_companion_emergency_photo_uploads", ["employer_id"])
    op.create_index("ix_patient_companion_emergency_photo_uploads_patient_id", "patient_companion_emergency_photo_uploads", ["patient_id"])
    op.create_index("ix_patient_companion_emergency_photo_uploads_status", "patient_companion_emergency_photo_uploads", ["status"])
    op.create_index("ix_patient_companion_emergency_photo_uploads_asset_id", "patient_companion_emergency_photo_uploads", ["asset_id"])

    op.create_table(
        "patient_companion_emergency_photo_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("upload_id", sa.Integer(), sa.ForeignKey("patient_companion_emergency_photo_uploads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_sha256", sa.String(length=64), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("upload_id", "chunk_index", name="uq_pc07_photo_chunk_upload_index"),
    )
    op.create_index("ix_pc07_photo_chunk_upload", "patient_companion_emergency_photo_chunks", ["upload_id"])
    op.create_index("ix_patient_companion_emergency_photo_chunks_upload_id", "patient_companion_emergency_photo_chunks", ["upload_id"])


def downgrade():
    op.drop_table("patient_companion_emergency_photo_chunks")
    op.drop_table("patient_companion_emergency_photo_uploads")
