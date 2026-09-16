"""Operator-only Alembic baseline for a genuinely empty PostgreSQL database.

The historical Digital Crown Alembic chain contains reconciliation revisions that
were generated against databases already modified by older runtime/manual schema
steps. Replaying those revisions from the root on a brand-new PostgreSQL database
therefore does not describe a valid transition.

This helper is deliberately narrow: only a completely empty PostgreSQL schema may
be materialized from the metadata snapshot of the exact checked-out code and
stamped to its exact unique Alembic head. Existing PostgreSQL databases always
continue through the normal revision chain and are never rebuilt or re-stamped.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData


ALEMBIC_VERSION_TABLE = "alembic_version"


def bootstrap_empty_postgresql_to_head(
    connection: Connection,
    metadata: MetaData,
    heads: Sequence[str],
) -> bool:
    """Materialize and stamp a genuinely empty PostgreSQL schema.

    Returns ``True`` only when the empty-schema baseline was created. Any
    non-PostgreSQL dialect or PostgreSQL schema containing a user table returns
    ``False`` so the normal Alembic revision chain remains authoritative.
    Ambiguous stamped-but-empty schemas fail closed instead of being guessed.
    """

    if connection.dialect.name != "postgresql":
        return False

    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names(schema="public"))
    user_tables = tables - {ALEMBIC_VERSION_TABLE}
    if user_tables:
        return False

    if ALEMBIC_VERSION_TABLE in tables:
        stamped = connection.execute(
            sa.text(f"SELECT version_num FROM {ALEMBIC_VERSION_TABLE}")
        ).scalars().all()
        if stamped:
            raise RuntimeError(
                "Empty PostgreSQL database already carries an Alembic revision; "
                "refusing to replace or guess its schema state"
            )

    unique_heads = tuple(dict.fromkeys(heads))
    if len(unique_heads) != 1 or not unique_heads[0]:
        raise RuntimeError(
            "PostgreSQL baseline requires exactly one Alembic head; "
            f"found {list(unique_heads)!r}"
        )
    head = unique_heads[0]

    # Explicit Alembic operator action only. Application startup never calls this.
    metadata.create_all(bind=connection, checkfirst=False)

    actual_tables = set(sa.inspect(connection).get_table_names(schema="public"))
    expected_tables = {
        table.name
        for table in metadata.sorted_tables
        if table.schema in (None, "public")
    }
    missing = expected_tables - actual_tables
    if missing:
        raise RuntimeError(
            "PostgreSQL baseline schema verification failed; missing tables: "
            + ", ".join(sorted(missing))
        )

    connection.execute(
        sa.text(
            "CREATE TABLE IF NOT EXISTS alembic_version "
            "(version_num VARCHAR(32) NOT NULL PRIMARY KEY)"
        )
    )
    existing_versions = connection.execute(
        sa.text("SELECT version_num FROM alembic_version")
    ).scalars().all()
    if existing_versions:
        raise RuntimeError(
            "Alembic version table became non-empty during PostgreSQL baseline; "
            "refusing to overwrite it"
        )
    connection.execute(
        sa.text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": head},
    )

    return True
