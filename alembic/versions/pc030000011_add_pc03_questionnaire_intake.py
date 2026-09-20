"""add Patient Companion medical questionnaire intake

Revision ID: pc030000011
Revises: pc020000010
"""

from alembic import op
import sqlalchemy as sa

revision = "pc030000011"
down_revision = "pc020000010"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient_companion_questionnaire_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("lineage_key", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("questions_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("retired_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("employer_id", "lineage_key", "version", name="uq_pc_questionnaire_definition_lineage_version"),
    )
    op.create_index("ix_pc_questionnaire_definition_public_id", "patient_companion_questionnaire_definitions", ["public_id"], unique=True)
    op.create_index("ix_pc_questionnaire_definition_employer_id", "patient_companion_questionnaire_definitions", ["employer_id"], unique=False)
    op.create_index("ix_pc_questionnaire_definition_lineage_key", "patient_companion_questionnaire_definitions", ["lineage_key"], unique=False)
    op.create_index("ix_pc_questionnaire_definition_status", "patient_companion_questionnaire_definitions", ["status"], unique=False)
    op.create_index("ix_pc_questionnaire_definition_tenant_status", "patient_companion_questionnaire_definitions", ["employer_id", "status"], unique=False)

    op.create_table(
        "patient_companion_questionnaire_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("questionnaire_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["questionnaire_id"], ["patient_companion_questionnaire_definitions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_id"),
        sa.UniqueConstraint("employer_id", "patient_id", "questionnaire_id", name="uq_pc_questionnaire_assignment_patient_version"),
    )
    for name, cols, unique in [
        ("ix_pc_questionnaire_assignment_public_id", ["public_id"], True),
        ("ix_pc_questionnaire_assignment_employer_id", ["employer_id"], False),
        ("ix_pc_questionnaire_assignment_patient_id", ["patient_id"], False),
        ("ix_pc_questionnaire_assignment_questionnaire_id", ["questionnaire_id"], False),
        ("ix_pc_questionnaire_assignment_status", ["status"], False),
        ("ix_pc_questionnaire_assignment_expires_at", ["expires_at"], False),
        ("ix_pc_questionnaire_assignment_revoked_at", ["revoked_at"], False),
        ("ix_pc_questionnaire_assignment_tenant_patient_status", ["employer_id", "patient_id", "status"], False),
    ]:
        op.create_index(name, "patient_companion_questionnaire_assignments", cols, unique=unique)

    op.create_table(
        "patient_companion_questionnaire_submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=36), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("access_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("questionnaire_id", sa.Integer(), nullable=False),
        sa.Column("answers_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["access_id"], ["patient_companion_accesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assignment_id"], ["patient_companion_questionnaire_assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["questionnaire_id"], ["patient_companion_questionnaire_definitions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", name="uq_pc_questionnaire_submission_assignment"),
        sa.UniqueConstraint("public_id"),
    )
    for name, cols, unique in [
        ("ix_pc_questionnaire_submission_public_id", ["public_id"], True),
        ("ix_pc_questionnaire_submission_assignment_id", ["assignment_id"], False),
        ("ix_pc_questionnaire_submission_access_id", ["access_id"], False),
        ("ix_pc_questionnaire_submission_employer_id", ["employer_id"], False),
        ("ix_pc_questionnaire_submission_patient_id", ["patient_id"], False),
        ("ix_pc_questionnaire_submission_questionnaire_id", ["questionnaire_id"], False),
        ("ix_pc_questionnaire_submission_status", ["status"], False),
        ("ix_pc_questionnaire_submission_tenant_status", ["employer_id", "status"], False),
    ]:
        op.create_index(name, "patient_companion_questionnaire_submissions", cols, unique=unique)


def downgrade():
    for name in [
        "ix_pc_questionnaire_submission_tenant_status", "ix_pc_questionnaire_submission_status",
        "ix_pc_questionnaire_submission_questionnaire_id", "ix_pc_questionnaire_submission_patient_id",
        "ix_pc_questionnaire_submission_employer_id", "ix_pc_questionnaire_submission_access_id",
        "ix_pc_questionnaire_submission_assignment_id", "ix_pc_questionnaire_submission_public_id",
    ]:
        op.drop_index(name, table_name="patient_companion_questionnaire_submissions")
    op.drop_table("patient_companion_questionnaire_submissions")
    for name in [
        "ix_pc_questionnaire_assignment_tenant_patient_status", "ix_pc_questionnaire_assignment_revoked_at",
        "ix_pc_questionnaire_assignment_expires_at", "ix_pc_questionnaire_assignment_status",
        "ix_pc_questionnaire_assignment_questionnaire_id", "ix_pc_questionnaire_assignment_patient_id",
        "ix_pc_questionnaire_assignment_employer_id", "ix_pc_questionnaire_assignment_public_id",
    ]:
        op.drop_index(name, table_name="patient_companion_questionnaire_assignments")
    op.drop_table("patient_companion_questionnaire_assignments")
    for name in [
        "ix_pc_questionnaire_definition_tenant_status", "ix_pc_questionnaire_definition_status",
        "ix_pc_questionnaire_definition_lineage_key", "ix_pc_questionnaire_definition_employer_id",
        "ix_pc_questionnaire_definition_public_id",
    ]:
        op.drop_index(name, table_name="patient_companion_questionnaire_definitions")
    op.drop_table("patient_companion_questionnaire_definitions")
