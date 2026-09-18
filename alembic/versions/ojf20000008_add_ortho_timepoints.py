"""Add Ortho Journey F2 reference-only timepoints.

Revision ID: ojf20000008
Revises: ojf1b000007
"""

from alembic import op
import sqlalchemy as sa


revision = "ojf20000008"
down_revision = "ojf1b000007"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ortho_timepoints",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ortho_case_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("ordinal >= 0 AND ordinal <= 999", name="ck_ortho_timepoints_ordinal"),
        sa.ForeignKeyConstraint(["ortho_case_id"], ["ortho_cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ortho_timepoints_id", "ortho_timepoints", ["id"], unique=False)
    op.create_index("ix_ortho_timepoints_ortho_case_id", "ortho_timepoints", ["ortho_case_id"], unique=False)
    op.create_index("ix_ortho_timepoints_employer_id", "ortho_timepoints", ["employer_id"], unique=False)
    op.create_index("ix_ortho_timepoints_patient_id", "ortho_timepoints", ["patient_id"], unique=False)
    op.create_index("ix_ortho_timepoints_occurred_at", "ortho_timepoints", ["occurred_at"], unique=False)
    op.create_index(
        "uq_ortho_timepoints_case_ordinal",
        "ortho_timepoints",
        ["ortho_case_id", "ordinal"],
        unique=True,
    )
    op.create_index(
        "ix_ortho_timepoints_employer_patient_occurred",
        "ortho_timepoints",
        ["employer_id", "patient_id", "occurred_at"],
        unique=False,
    )

    op.create_table(
        "ortho_timepoint_evidences",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("ortho_timepoint_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("clinical_asset_id", sa.Integer(), nullable=True),
        sa.Column("cephalo_analysis_id", sa.Integer(), nullable=True),
        sa.Column("panoramic_analysis_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(CASE WHEN clinical_asset_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN cephalo_analysis_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN panoramic_analysis_id IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_ortho_timepoint_evidence_exactly_one_source",
        ),
        sa.ForeignKeyConstraint(["ortho_timepoint_id"], ["ortho_timepoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinical_asset_id"], ["clinical_assets.id"]),
        sa.ForeignKeyConstraint(["cephalo_analysis_id"], ["cephalo_analyses.id"]),
        sa.ForeignKeyConstraint(["panoramic_analysis_id"], ["panoramic_analyses.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ortho_timepoint_evidences_id", "ortho_timepoint_evidences", ["id"], unique=False)
    op.create_index("ix_ortho_timepoint_evidences_ortho_timepoint_id", "ortho_timepoint_evidences", ["ortho_timepoint_id"], unique=False)
    op.create_index("ix_ortho_timepoint_evidences_employer_id", "ortho_timepoint_evidences", ["employer_id"], unique=False)
    op.create_index("ix_ortho_timepoint_evidences_patient_id", "ortho_timepoint_evidences", ["patient_id"], unique=False)
    op.create_index("ix_ortho_timepoint_evidences_clinical_asset_id", "ortho_timepoint_evidences", ["clinical_asset_id"], unique=False)
    op.create_index("ix_ortho_timepoint_evidences_cephalo_analysis_id", "ortho_timepoint_evidences", ["cephalo_analysis_id"], unique=False)
    op.create_index("ix_ortho_timepoint_evidences_panoramic_analysis_id", "ortho_timepoint_evidences", ["panoramic_analysis_id"], unique=False)
    op.create_index(
        "uq_ortho_timepoint_evidence_asset",
        "ortho_timepoint_evidences",
        ["clinical_asset_id"],
        unique=True,
    )
    op.create_index(
        "uq_ortho_timepoint_evidence_cephalo",
        "ortho_timepoint_evidences",
        ["cephalo_analysis_id"],
        unique=True,
    )
    op.create_index(
        "uq_ortho_timepoint_evidence_panoramic",
        "ortho_timepoint_evidences",
        ["panoramic_analysis_id"],
        unique=True,
    )


def downgrade():
    op.drop_table("ortho_timepoint_evidences")
    op.drop_table("ortho_timepoints")
