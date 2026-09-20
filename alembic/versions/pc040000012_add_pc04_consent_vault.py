"""PC-04 patient-facing Consent Vault evidence.

Revision ID: pc040000012
Revises: pc030000011
"""

from alembic import op
import sqlalchemy as sa


revision = "pc040000012"
down_revision = "pc030000011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_companion_consent_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("document_archives.id", ondelete="CASCADE"), nullable=False),
        sa.Column("share_grant_id", sa.Integer(), sa.ForeignKey("patient_companion_share_grants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_group_id", sa.String(length=64), nullable=False),
        sa.Column("document_version", sa.Integer(), nullable=False),
        sa.Column("document_file_hash", sa.String(length=64), nullable=False),
        sa.Column("document_file_size", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "employer_id", "patient_id", "document_id", "document_file_hash",
            name="uq_pc_consent_request_patient_document_hash",
        ),
    )
    op.create_index("ix_patient_companion_consent_requests_public_id", "patient_companion_consent_requests", ["public_id"], unique=True)
    op.create_index("ix_pc_consent_request_tenant_patient_status", "patient_companion_consent_requests", ["employer_id", "patient_id", "status"])
    op.create_index("ix_patient_companion_consent_requests_document_id", "patient_companion_consent_requests", ["document_id"])
    op.create_index("ix_patient_companion_consent_requests_share_grant_id", "patient_companion_consent_requests", ["share_grant_id"])
    op.create_index("ix_patient_companion_consent_requests_expires_at", "patient_companion_consent_requests", ["expires_at"])
    op.create_index("ix_patient_companion_consent_requests_revoked_at", "patient_companion_consent_requests", ["revoked_at"])

    op.create_table(
        "patient_companion_consent_evidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("consent_request_id", sa.Integer(), sa.ForeignKey("patient_companion_consent_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("access_id", sa.Integer(), sa.ForeignKey("patient_companion_accesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signature_png", sa.LargeBinary(), nullable=False),
        sa.Column("signature_sha256", sa.String(length=64), nullable=False),
        sa.Column("signature_size", sa.Integer(), nullable=False),
        sa.Column("signed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("consent_request_id", name="uq_pc_consent_evidence_request"),
    )
    op.create_index("ix_patient_companion_consent_evidence_public_id", "patient_companion_consent_evidence", ["public_id"], unique=True)
    op.create_index("ix_patient_companion_consent_evidence_consent_request_id", "patient_companion_consent_evidence", ["consent_request_id"])
    op.create_index("ix_patient_companion_consent_evidence_access_id", "patient_companion_consent_evidence", ["access_id"])
    op.create_index("ix_pc_consent_evidence_tenant_signed", "patient_companion_consent_evidence", ["employer_id", "signed_at"])


def downgrade():
    op.drop_table("patient_companion_consent_evidence")
    op.drop_table("patient_companion_consent_requests")
