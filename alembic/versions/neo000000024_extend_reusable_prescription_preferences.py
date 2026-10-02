"""extend reusable prescription preferences for Neo quick access

Revision ID: neo000000024
Revises: neo000000023
Create Date: 2026-09-30
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000024"
down_revision = "neo000000023"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("doctor_prescription_preferences", sa.Column("label", sa.String(length=100), nullable=True))
    op.add_column(
        "doctor_prescription_preferences",
        sa.Column("preference_type", sa.String(length=32), nullable=False, server_default="PROTOCOL"),
    )
    op.add_column("doctor_prescription_preferences", sa.Column("indication", sa.Text(), nullable=True))
    op.add_column(
        "doctor_prescription_preferences",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "doctor_prescription_preferences",
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("doctor_prescription_preferences", sa.Column("last_used", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_doctor_prescription_preferences_preference_type",
        "doctor_prescription_preferences",
        ["preference_type"],
        unique=False,
    )
    op.create_index(
        "ix_doctor_prescription_preferences_is_favorite",
        "doctor_prescription_preferences",
        ["is_favorite"],
        unique=False,
    )
    op.create_index(
        "ix_doctor_prescription_preferences_last_used",
        "doctor_prescription_preferences",
        ["last_used"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_doctor_prescription_preferences_last_used", table_name="doctor_prescription_preferences")
    op.drop_index("ix_doctor_prescription_preferences_is_favorite", table_name="doctor_prescription_preferences")
    op.drop_index("ix_doctor_prescription_preferences_preference_type", table_name="doctor_prescription_preferences")
    op.drop_column("doctor_prescription_preferences", "last_used")
    op.drop_column("doctor_prescription_preferences", "usage_count")
    op.drop_column("doctor_prescription_preferences", "is_favorite")
    op.drop_column("doctor_prescription_preferences", "indication")
    op.drop_column("doctor_prescription_preferences", "preference_type")
    op.drop_column("doctor_prescription_preferences", "label")
