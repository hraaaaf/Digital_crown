"""Add patient_id to bot_sessions for per-patient conversation history

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-16 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bot_sessions',
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id', ondelete='SET NULL'), nullable=True, index=True)
    )


def downgrade() -> None:
    op.drop_column('bot_sessions', 'patient_id')
