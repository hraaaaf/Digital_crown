"""Track one-time V7.1 reference catalog installation per cabinet.

Revision ID: v7100000019
Revises: v7100000018
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "v7100000019"
down_revision: Union[str, Sequence[str], None] = "v7100000018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cabinet_catalog_reference_state",
        sa.Column(
            "employer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("version", sa.String(length=40), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cabinet_catalog_reference_state")
