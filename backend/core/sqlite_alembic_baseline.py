"""Operator-only Alembic baseline for a genuinely empty SQLite database.

This module is intentionally not imported by application startup.  It exists so
``alembic upgrade head`` can initialize a new SQLite/SQLCipher cabinet from the
metadata snapshot belonging to the exact code revision being executed, without
replaying PostgreSQL-specific historical reconciliation migrations.

Existing databases are never stamped or rebuilt here: as soon as a user table is
present, the normal Alembic revision chain remains authoritative.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.engine import Connection
from sqlalchemy.schema import MetaData


ALEMBIC_VERSION_TABLE = "alembic_version"


def _user_tables(connection: Connection) -> set[str]:
    return set(sa.inspect(connection).get_table_names()) - {ALEMBIC_VERSION_TABLE}


def bootstrap_empty_sqlite_to_head(
    connection: Connection,
    metadata: MetaData,
    heads: Sequence[str],
) -> bool:
    """Materialize and stamp an empty SQLite/SQLCipher database.

    Returns ``True`` only when a baseline was created.  PostgreSQL and non-empty
    SQLite databases return ``False`` and continue through the regular revision
    chain.  Ambiguous/malformed empty databases fail closed instead of guessing.
    """

    if connection.dialect.name != "sqlite":
        return False

    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    user_tables = tables - {ALEMBIC_VERSION_TABLE}
    if user_tables:
        return False

    if ALEMBIC_VERSION_TABLE in tables:
        stamped = connection.execute(
            sa.text(f"SELECT version_num FROM {ALEMBIC_VERSION_TABLE}")
        ).scalars().all()
        if stamped:
            raise RuntimeError(
                "Empty SQLite database already carries an Alembic revision; "
                "refusing to replace or guess its schema state"
            )

    unique_heads = tuple(dict.fromkeys(heads))
    if len(unique_heads) != 1 or not unique_heads[0]:
        raise RuntimeError(
            "SQLite baseline requires exactly one Alembic head; "
            f"found {list(unique_heads)!r}"
        )
    head = unique_heads[0]

    # This is an Alembic operator action, not an application-startup side effect.
    # The exact checked-out code revision supplies the schema snapshot; the exact
    # Alembic head is persisted below so every subsequent upgrade remains versioned.
    metadata.create_all(bind=connection, checkfirst=False)

    actual_tables = set(sa.inspect(connection).get_table_names())
    expected_tables = {table.name for table in metadata.sorted_tables}
    missing = expected_tables - actual_tables
    if missing:
        raise RuntimeError(
            "SQLite baseline schema verification failed; missing tables: "
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
            "Alembic version table became non-empty during SQLite baseline; "
            "refusing to overwrite it"
        )
    connection.execute(
        sa.text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": head},
    )

    return True
