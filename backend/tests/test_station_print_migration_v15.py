"""Isolated Alembic candidate checks for LOT04.8-B2b.

Executes migration against a disposable SQLite schema with a synthetic users
table, NOT on a Cabinet database. No printer, patient or PDF content.
"""
from datetime import datetime, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import (
    Column, Integer, MetaData, Table, create_engine, inspect, insert, select,
)
from sqlalchemy.exc import IntegrityError

from backend.services.station_document_print_store import (
    audit, configuration, printers, stations,
)

MIGRATION = Path(__file__).with_name("migration_station_print_owner_config.py")
PRINT_TABLES = {
    "station_print_configurations", "station_print_config_stations",
    "station_print_config_printers", "station_print_config_audit",
}


def migration_module():
    spec = spec_from_file_location("dc_neo000000028_test_only", MIGRATION)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def migrated():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    bootstrap = MetaData()
    users = Table("users", bootstrap, Column("id", Integer, primary_key=True))
    bootstrap.create_all(engine)
    with engine.begin() as conn:
        conn.execute(insert(users), [{"id": 10}, {"id": 20}])
    conn = engine.connect()
    conn.exec_driver_sql("PRAGMA foreign_keys = ON")
    conn.commit()
    module = migration_module()
    module.op = Operations(MigrationContext.configure(conn))
    with conn.begin():
        module.upgrade()
    try:
        yield engine, conn, module
    finally:
        conn.close()
        engine.dispose()


def test_migration_is_attached_to_observed_station_alembic_head():
    module = migration_module()
    assert module.revision == "neo000000028"
    assert module.down_revision == "neo000000027"


def test_upgrade_adds_only_inert_print_tables(migrated):
    engine, conn, _ = migrated
    existing = set(inspect(engine).get_table_names())
    assert existing == PRINT_TABLES | {"users"}
    assert conn.execute(select(configuration.c.tenant_id)).all() == []
    assert conn.execute(select(audit.c.id)).all() == []


def _configuration(conn, tenant=10, mode="reception", revision=1):
    conn.execute(insert(configuration).values(
        tenant_id=tenant, mode=mode, revision=revision,
        updated_by_user_id=tenant, updated_at=datetime(2026, 10, 13, tzinfo=timezone.utc),
    ))


def test_default_is_disabled_for_new_row_and_no_foreign_tenant(migrated):
    _, conn, _ = migrated
    with conn.begin():
        conn.execute(insert(configuration).values(
            tenant_id=10, revision=1, updated_by_user_id=10,
            updated_at=datetime(2026, 10, 13, tzinfo=timezone.utc),
        ))
    assert conn.execute(select(configuration.c.mode)).scalar_one() == "disabled"
    conn.rollback()  # read started an implicit SQLAlchemy transaction
    with pytest.raises(IntegrityError):
        with conn.begin():
            _configuration(conn, tenant=99)


@pytest.mark.parametrize("mode,revision", [
    ("untrusted", 1), ("reception", 0), ("both", -1),
])
def test_database_enforces_mode_and_revision_constraints(migrated, mode, revision):
    _, conn, _ = migrated
    with pytest.raises(IntegrityError):
        with conn.begin():
            _configuration(conn, mode=mode, revision=revision)
    assert conn.execute(select(configuration.c.tenant_id)).all() == []


def test_unique_tenant_and_unique_target_constraints(migrated):
    _, conn, _ = migrated
    with conn.begin():
        _configuration(conn)
        conn.execute(insert(stations).values(tenant_id=10, station_id="station-a"))
        conn.execute(insert(printers).values(tenant_id=10, printer_id="desk-a"))
    for table, values in [
        (configuration, dict(tenant_id=10, mode="disabled", revision=2, updated_by_user_id=10,
                             updated_at=datetime(2026, 10, 13, tzinfo=timezone.utc))),
        (stations, dict(tenant_id=10, station_id="station-a")),
        (printers, dict(tenant_id=10, printer_id="desk-a")),
    ]:
        with pytest.raises(IntegrityError):
            with conn.begin():
                conn.execute(insert(table).values(**values))
    assert conn.execute(select(configuration.c.revision)).scalar_one() == 1


def test_foreign_configuration_required_for_allowlist_targets(migrated):
    _, conn, _ = migrated
    for table, values in [
        (stations, dict(tenant_id=10, station_id="station-missing")),
        (printers, dict(tenant_id=10, printer_id="printer-missing")),
    ]:
        with pytest.raises(IntegrityError):
            with conn.begin():
                conn.execute(insert(table).values(**values))


def test_allowlist_rows_are_removed_when_config_deleted_but_audit_remains(migrated):
    _, conn, _ = migrated
    from sqlalchemy import delete
    with conn.begin():
        _configuration(conn)
        conn.execute(insert(stations).values(tenant_id=10, station_id="station-a"))
        conn.execute(insert(printers).values(tenant_id=10, printer_id="printer-a"))
        conn.execute(insert(audit).values(
            tenant_id=10, revision=1, actor_user_id=10, mode="reception",
            changed_at=datetime(2026, 10, 13, tzinfo=timezone.utc),
        ))
    with conn.begin():
        conn.execute(delete(configuration).where(configuration.c.tenant_id == 10))
    assert conn.execute(select(stations.c.station_id)).all() == []
    assert conn.execute(select(printers.c.printer_id)).all() == []
    assert conn.execute(select(audit.c.id)).all() != []


def test_downgrade_preserves_existing_user_table(migrated):
    engine, conn, module = migrated
    with conn.begin():
        module.downgrade()
    remaining = set(inspect(engine).get_table_names())
    assert remaining == {"users"}
    assert conn.execute(select(Table("users", MetaData(), autoload_with=conn).c.id)).all() == [(10,), (20,)]
