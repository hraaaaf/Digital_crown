import os
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context
from alembic.script import ScriptDirectory
from backend.core.postgresql_alembic_baseline import bootstrap_empty_postgresql_to_head
from backend.core.sqlite_alembic_baseline import bootstrap_empty_sqlite_to_head
from backend.models import Base
from backend import models_patient_companion as _models_patient_companion  # noqa: F401
from backend import models_patient_companion_notifications as _models_patient_companion_notifications  # noqa: F401
# The catalog tables are declared by the service module rather than the legacy
# model module. Importing the module registers metadata only; schema creation is
# still performed solely by versioned Alembic operator actions.
from backend.services import cabinet_catalog_store as _cabinet_catalog_store  # noqa: F401
# LOT04.8: the empty-PostgreSQL/SQLite Alembic operator baseline uses
# Base.metadata (not a replay of revision scripts). Register ONLY these
# migration-defined printer configuration tables in that metadata so a fresh
# baseline cannot claim neo000000028 while missing its tables and audit index.
# No DDL here, and the isolated store's synthetic 'users' stub is NOT cloned.
from backend.services.station_document_print_store import schema as _station_print_schema
for _print_table_name in (
    "station_print_configurations",
    "station_print_config_stations",
    "station_print_config_printers",
    "station_print_config_audit",
):
    if _print_table_name not in Base.metadata.tables:
        _station_print_schema.tables[_print_table_name].to_metadata(Base.metadata)

# LOT04.8 staged B/C schemas. Real PostgreSQL/SQLite empty-baseline
# initialization STAMPS the current head from Base.metadata instead of
# replaying revisions. Clone both unprivileged, default-inert tables here
# so neither a new DB nor an existing neo28->29 upgrade can falsely report
# current schema while missing a table. The synthetic users stub is excluded.
from backend.services.station_print_printer_draft_lab import SCHEMA as _printer_draft_schema
from backend.services.station_print_held_claims_lab import SCHEMA as _held_claim_schema
for _table_name, _source_schema in (
    ("station_print_printer_drafts", _printer_draft_schema),
    ("station_print_held_claims", _held_claim_schema),
    ("station_print_claim_events", _held_claim_schema),
):
    if _table_name not in Base.metadata.tables:
        _source_schema.tables[_table_name].to_metadata(Base.metadata)


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

    Genuinely empty SQLite/SQLCipher and PostgreSQL databases use explicit
    Alembic-operator baselines from the metadata snapshot of the exact checked-out
    code and are stamped to the exact unique head. Existing databases always run
    the normal revision chain and are never rebuilt or re-stamped.

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

        if connection.dialect.name == "postgresql":
            with connection.begin():
                baselined = bootstrap_empty_postgresql_to_head(
                    connection,
                    target_metadata,
                    heads,
                )
            if baselined:
                return

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
