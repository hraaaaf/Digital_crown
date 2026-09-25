"""Merge the V1-07 integration head with PC-09 teleconsultation.

Revision ID: v1070000017
Revises: v1070000016, pc090000016
"""

from typing import Sequence, Union

revision: str = "v1070000017"
down_revision: tuple[str, str] = ("v1070000016", "pc090000016")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
