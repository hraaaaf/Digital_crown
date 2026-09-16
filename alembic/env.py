import os
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context
from alembic.script import ScriptDirectory
from backend.core.sqlite_alembic_baseline import bootstrap_empty_sqlite_to_head
from backend.models import Base
# The catalog tables are declared by the service module rather than the legacy
# model module. Importing the module registers metadata only; schema creation is
# still performed solely by versioned Alembic migrations.
from backend.services import cabinet_catalog_store as _cabinet_catalog_store  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata


def _explicit_postgresql_url() -> str | None:
    """Return the operator-supplied PostgreSQL URL without importing app runtime.

    PostgreSQL schema upgrades must remain migration-boundary operations. Importing
    ``backend.database`` here would pull password/runtime dependencies and startup
    preparation into Alembic before a migration has even begun. SQLite/SQLCipher
    deliberately keep the existing backend database path because their encrypted
    connection preparation is application-specific.
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.lower().startswith(("postgresql://", "postgresql+")):
        return url
    return None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _explicit_postgresql_url()
    if url is None:
        from backend.database import SQLALCHEMY_DATABASE_URL

        url = SQLALCHEMY_DATABASE_URL

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    New, genuinely empty SQLite/SQLCipher databases use an operator-only
    metadata baseline stamped to the exact unique Alembic head. Existing SQLite
    databases and PostgreSQL always execute the normal revision chain.

    PostgreSQL is connected directly from the explicit operator DATABASE_URL so
    Alembic does not import the application database runtime merely to migrate a
    schema. SQLite/SQLCipher retain the backend engine because their encrypted
    connection setup is application-specific.
    """
    postgres_url = _explicit_postgresql_url()
    if postgres_url is not None:
        connectable = create_engine(postgres_url, poolclass=pool.NullPool)
    else:
        from backend.database import engine

        connectable = engine

    with connectable.connect() as connection:
        heads = ScriptDirectory.from_config(config).get_heads()
        if connection.dialect.name == "sqlite":
            with connection.begin():
                baselined = bootstrap_empty_sqlite_to_head(
                    connection,
                    target_metadata,
                    heads,
                )
            if baselined:
                return

        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
