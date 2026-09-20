"""Read-only schema gate used before a cabinet/rehearsal application boot."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text


# Updated together with the last migration in this repository.  A stale cabinet
# must be upgraded explicitly before the application is allowed to open normally.
CURRENT_ALEMBIC_HEAD = "pc040000012"


def assert_database_at_current_head(engine, expected_head: str = CURRENT_ALEMBIC_HEAD) -> None:
    """Fail closed if the DB is not already at the versioned schema head.

    This deliberately performs no migration and no write.  The operator/install
    workflow must run Alembic separately, with its own backup and rehearsal gates.
    """
    # A normal SQLite connection creates a missing file on connect. Refuse that
    # side effect: an empty/new cabinet must be initialized by an explicit Alembic
    # invocation, never by application boot.
    if engine.dialect.name == "sqlite":
        database = str(getattr(engine.url, "database", "") or "")
        if database and database != ":memory:" and not database.startswith("file:"):
            database_path = Path(database).expanduser()
            if not database_path.is_absolute():
                database_path = Path.cwd() / database_path
            if not database_path.is_file():
                raise RuntimeError(
                    f"SECURITE : fichier SQLite absent ({database_path}); "
                    f"exécutez explicitement upgrade head vers {expected_head}."
                )

    with engine.connect() as connection:
        transaction = connection.begin()
        # PostgreSQL can enforce read-only at transaction level. SQLite/SQLCipher
        # has no portable equivalent; this function still issues SELECT only and
        # always rolls the transaction back.
        if connection.dialect.name == "postgresql":
            connection.execute(text("SET TRANSACTION READ ONLY"))
        versions = {
            str(value)
            for value in connection.execute(text("SELECT version_num FROM alembic_version")).scalars()
        }
        transaction.rollback()

    if versions != {expected_head}:
        actual = ",".join(sorted(versions)) or "<missing>"
        raise RuntimeError(
            f"SECURITE : schema Alembic non courant ({actual}); "
            f"exécutez explicitement upgrade head vers {expected_head}."
        )
