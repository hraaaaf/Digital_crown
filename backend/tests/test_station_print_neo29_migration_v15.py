"""Check synthetic neo000000028 -> 029 -> 028 migration contract.

The real PostgreSQL system-level gate is separate. This SQLite test exercises
version-script DDL only in an ephemeral, non-clinical database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import Column, Integer, MetaData, Table, create_engine, event, inspect, insert, select, text
from sqlalchemy.exc import IntegrityError

MIGRATION = Path(__file__).with_name("migration_station_print_neo29.py")


def load_migration():
    spec = spec_from_file_location("dc_neo29_lab", MIGRATION)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    @event.listens_for(engine, "connect")
    def enable_fk(raw, _record):
        raw.execute("PRAGMA foreign_keys=ON")
    # Represents two existing tables at predecessor neo28. No patient data.
    meta = MetaData()
    users = Table("users", meta, Column("id", Integer, primary_key=True))
    Table("station_print_configurations", meta, Column("tenant_id", Integer, primary_key=True))
    meta.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(users).values(id=10))
    yield engine
    engine.dispose()


def run(db, direction):
    module = load_migration()
    assert module.revision == "neo000000029"
    assert module.down_revision == "neo000000028"
    with db.begin() as connection:
        module.op = Operations(MigrationContext.configure(connection))
        getattr(module, direction)()


def test_upgrade_creates_inert_staged_tables_without_seed_rows(db):
    run(db, "upgrade")
    inspector = inspect(db)
    assert {"users", "station_print_configurations", "station_print_printer_drafts", "station_print_held_claims"} == set(inspector.get_table_names())
    for name in ("station_print_printer_drafts", "station_print_held_claims"):
        keys = inspector.get_foreign_keys(name)
        assert any(key["constrained_columns"] == ["tenant_id"] and key["referred_table"] == "users" for key in keys)
        with db.connect() as conn:
            assert conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar_one() == 0


def test_tenant_fk_and_claim_state_fail_closed(db):
    run(db, "upgrade")
    with pytest.raises(IntegrityError):
        with db.begin() as conn:
            conn.execute(text(
                "INSERT INTO station_print_held_claims "
                "(tenant_id,delivery_key,first_printer_id,revision,created_at,updated_at) "
                "VALUES (999,:key,'desk',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
            ), {"key": "a"*64})
    with db.begin() as conn:
        conn.execute(text(
            "INSERT INTO station_print_held_claims "
            "(tenant_id,delivery_key,first_printer_id,revision,created_at,updated_at) "
            "VALUES (10,:key,'desk',1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"
        ), {"key": "a"*64})
    with db.connect() as conn:
        assert conn.execute(text("SELECT state FROM station_print_held_claims")).scalar_one() == "held"
    with pytest.raises(IntegrityError):
        with db.begin() as conn:
            conn.execute(text(
                "UPDATE station_print_held_claims SET state='completed' WHERE tenant_id=10"
            ))


def test_downgrade_preserves_preexisting_tables(db):
    run(db, "upgrade")
    run(db, "downgrade")
    assert set(inspect(db).get_table_names()) == {"users", "station_print_configurations"}
    with db.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 1
