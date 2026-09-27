"""Add configurable applicability metadata to cabinet catalog acts.

Revision ID: v7100000018
Revises: v1070000017
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "v7100000018"
down_revision: Union[str, Sequence[str], None] = "v1070000017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cabinet_catalog_acts",
        sa.Column("applicability_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cabinet_catalog_acts", "applicability_json")
