"""G5 LAB: optional editable manual skin-profile handles (no clinical promotion).

Revision ID: neo000000035
Revises: neo000000034
"""
from alembic import op
import sqlalchemy as sa

revision = "neo000000035"
down_revision = "neo000000034"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "ortho_anatomical_traces",
        sa.Column("bezier_profile_json", sa.JSON(), nullable=True),
    )

def downgrade():
    op.drop_column("ortho_anatomical_traces", "bezier_profile_json")
