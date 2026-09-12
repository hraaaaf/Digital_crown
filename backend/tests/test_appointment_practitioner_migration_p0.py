import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, inspect


def _load_migration_module():
    path = Path("alembic/versions/d3a55e700003_add_appointment_praticien.py")
    spec = importlib.util.spec_from_file_location("appointment_practitioner_p0_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_appointment_practitioner_migration_upgrade_and_downgrade():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table("users", metadata, Column("id", Integer, primary_key=True))
    Table("appointments", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    migration = _load_migration_module()

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        migration.op = Operations(context)

        migration.upgrade()
        inspector = inspect(connection)
        columns = {column["name"]: column for column in inspector.get_columns("appointments")}
        assert "praticien_id" in columns
        assert columns["praticien_id"]["nullable"] is True
        assert any(
            fk["referred_table"] == "users"
            and fk["constrained_columns"] == ["praticien_id"]
            for fk in inspector.get_foreign_keys("appointments")
        )
        assert any(
            index["name"] == "ix_appointments_praticien_id"
            and index["column_names"] == ["praticien_id"]
            for index in inspector.get_indexes("appointments")
        )

        migration.downgrade()
        inspector = inspect(connection)
        assert "praticien_id" not in {
            column["name"] for column in inspector.get_columns("appointments")
        }
