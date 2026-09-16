from logging.config import fileConfig

from sqlalchemy import engine_from_config
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

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """
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
