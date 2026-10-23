"""Add tenant-bound, revision-locked orthodontic practitioner note approvals.

Revision ID: neo000000033
Revises: neo000000032
Additive migration only, supports SQLite/SQLCipher and PostgreSQL.
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000033"
down_revision = "neo000000032"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "ortho_bilan_practitioner_notes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("cephalo_analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("analysis_revision", sa.Integer(), nullable=False),
        sa.Column("study_digest", sa.String(64), nullable=False),
        sa.Column("draft_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes_json", sa.JSON(), nullable=False),
        sa.Column("drafted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("approved_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approved_digest", sa.String(64), nullable=True),
        sa.UniqueConstraint("analysis_id", name="uq_ortho_bilan_practitioner_analysis"),
    )
    op.create_index("ix_ortho_bilan_notes_cabinet_patient",
                    "ortho_bilan_practitioner_notes", ["employer_id", "patient_id"])

def downgrade():
    op.drop_index("ix_ortho_bilan_notes_cabinet_patient", table_name="ortho_bilan_practitioner_notes")
    op.drop_table("ortho_bilan_practitioner_notes")
