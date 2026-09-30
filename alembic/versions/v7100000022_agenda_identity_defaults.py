"""Add PostgreSQL identity defaults for legacy Agenda primary keys.

Revision ID: v7100000022
Revises: v7100000021
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "v7100000022"
down_revision: Union[str, None] = "v7100000021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_pg_pk_default(bind, table: str) -> None:
    if bind.dialect.name != "postgresql":
        return

    sequence = f"{table}_id_seq"
    preparer = bind.dialect.identifier_preparer
    q_table = preparer.quote(table)
    q_sequence = preparer.quote(sequence)

    bind.execute(sa.text(f"CREATE SEQUENCE IF NOT EXISTS {q_sequence}"))
    bind.execute(sa.text(
        f"SELECT setval('{sequence}', "
        f"GREATEST(COALESCE((SELECT MAX(id) FROM {q_table}), 0) + 1, 1), false)"
    ))
    bind.execute(sa.text(
        f"ALTER TABLE {q_table} ALTER COLUMN id SET DEFAULT nextval('{sequence}')"
    ))
    bind.execute(sa.text(
        f"ALTER SEQUENCE {q_sequence} OWNED BY {q_table}.id"
    ))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    for table in ("cabinet_settings", "agenda_exceptions"):
        if not inspector.has_table(table):
            raise RuntimeError(f"Required schema table is missing: {table}")
        _ensure_pg_pk_default(bind, table)


def downgrade() -> None:
    # Removing a live primary-key generator is intentionally not automated.
    pass
