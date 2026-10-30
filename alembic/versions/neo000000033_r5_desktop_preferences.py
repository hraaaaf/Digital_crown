"""R5 07-D — add nonclinical workstation-bound preferences.

Revision ID: neo000000033
Revises: neo000000032
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000033"
down_revision = "neo000000032"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "r5_desktop_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workstation_id", sa.String(length=36), sa.ForeignKey("workstation_modes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("previous_payload", sa.JSON(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("employer_id","user_id","workstation_id",name="uq_r5_pref_principal_station"),
    )
    op.create_index("ix_r5_desktop_preferences_employer_id", "r5_desktop_preferences", ["employer_id"])
    op.create_index("ix_r5_desktop_preferences_user_id", "r5_desktop_preferences", ["user_id"])
    op.create_index("ix_r5_desktop_preferences_workstation_id", "r5_desktop_preferences", ["workstation_id"])

def downgrade():
    op.drop_index("ix_r5_desktop_preferences_workstation_id",table_name="r5_desktop_preferences")
    op.drop_index("ix_r5_desktop_preferences_user_id",table_name="r5_desktop_preferences")
    op.drop_index("ix_r5_desktop_preferences_employer_id",table_name="r5_desktop_preferences")
    op.drop_table("r5_desktop_preferences")
