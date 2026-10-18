"""Reserve cephalometric archive identity across simultaneous requests.

Revision ID: ceparch0001
Revises: v7100000022

This is deliberately additive. Existing archives are not backfilled or altered:
historical duplicates require explicit review, not automatic deduplication.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "ceparch0001"
down_revision: Union[str, None] = "v7100000022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cephalo_archive_claims",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("cephalo_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("document_archive_id", sa.Integer(), sa.ForeignKey("document_archives.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "patient_id", "analysis_id", "revision",
            name="uq_cephalo_archive_claim_study_revision",
        ),
    )
    op.create_index("ix_cephalo_archive_claims_patient_id", "cephalo_archive_claims", ["patient_id"])
    op.create_index("ix_cephalo_archive_claims_analysis_id", "cephalo_archive_claims", ["analysis_id"])


def downgrade() -> None:
    # Refuse destructive rollback: these rows protect medical document identity.
    raise RuntimeError("Clinical archive claim rollback requires an approved data-retention migration")
