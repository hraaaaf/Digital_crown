"""Add user_id to bot_sessions for per-user history isolation

Revision ID: a1b2c3d4e5f6
Revises: 74e675197637
Create Date: 2026-06-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '74e675197637'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bot_sessions',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    )


def downgrade() -> None:
    op.drop_column('bot_sessions', 'user_id')
