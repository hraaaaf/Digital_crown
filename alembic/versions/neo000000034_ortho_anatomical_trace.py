"""Add tenant-scoped, revision/image-locked G5 manual anatomical tracing.

Revision ID: neo000000034
Revises: neo000000033
Staged additive migration only. DO NOT apply to Production in G5 LAB phase.
"""
from alembic import op
import sqlalchemy as sa

revision="neo000000034"
down_revision="neo000000033"
branch_labels=None
depends_on=None


def upgrade():
    op.create_table(
        "ortho_anatomical_traces",
        sa.Column("id",sa.Integer(),primary_key=True),
        sa.Column("employer_id",sa.Integer(),
                  sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),
        sa.Column("patient_id",sa.Integer(),
                  sa.ForeignKey("patients.id",ondelete="CASCADE"),nullable=False),
        sa.Column("analysis_id",sa.Integer(),
                  sa.ForeignKey("cephalo_analyses.id",ondelete="CASCADE"),nullable=False),
        sa.Column("analysis_revision",sa.Integer(),nullable=False),
        sa.Column("scientific_digest",sa.String(64),nullable=False),
        sa.Column("image_sha256",sa.String(64),nullable=False),
        sa.Column("image_width",sa.Integer(),nullable=False),
        sa.Column("image_height",sa.Integer(),nullable=False),
        sa.Column("contour_digest",sa.String(64),nullable=False),
        sa.Column("contours_json",sa.JSON(),nullable=False),
        sa.Column("draft_version",sa.Integer(),server_default="1",nullable=False),
        sa.Column("drafted_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=False),
        sa.Column("updated_at",sa.DateTime(),nullable=False),
        sa.Column("approved_by",sa.Integer(),sa.ForeignKey("users.id"),nullable=True),
        sa.Column("approved_at",sa.DateTime(),nullable=True),
        sa.Column("approved_digest",sa.String(64),nullable=True),
        sa.UniqueConstraint("analysis_id",name="uq_ortho_anatomic_trace_analysis"),
    )
    op.create_index("ix_ortho_anatomic_trace_tenant_patient",
                    "ortho_anatomical_traces",["employer_id","patient_id"])


def downgrade():
    op.drop_index("ix_ortho_anatomic_trace_tenant_patient",
                  table_name="ortho_anatomical_traces")
    op.drop_table("ortho_anatomical_traces")
