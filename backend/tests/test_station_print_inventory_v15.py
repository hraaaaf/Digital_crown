"""LOT04.8-B2c: trusted DB Station lookup, no physical printer self-certification."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import (
    Column, DateTime, Integer, MetaData, String, Table,
    create_engine, insert, update,
)
from sqlalchemy.exc import OperationalError

from backend.services.station_document_print_configuration import (
    PrintConfigurationRejected, compile_owner_print_config,
)
from backend.services.station_document_print_inventory import (
    enrolled_stations_for_tenant,
    independently_certified_printers_for_tenant,
)
from backend.services.station_document_print_store import (
    load_effective_configuration, save_owner_configuration, schema,
)


@pytest.fixture
def cabinet():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    meta = MetaData()
    workstations = Table(
        "workstation_modes", meta,
        Column("id", String(36), primary_key=True),
        Column("employer_id", Integer, nullable=False),
        Column("default_experience", String(32)),
        Column("revoked_at", DateTime()),
    )
    meta.create_all(engine)
    schema.create_all(engine)  # LAB ONLY: no real cabinet touched
    with engine.begin() as connection:
        connection.execute(insert(workstations), [
            {"id": "station-1", "employer_id": 10, "default_experience": "station"},
            {"id": "station-foreign", "employer_id": 20, "default_experience": "station"},
            {"id": "cabinet-desk", "employer_id": 10, "default_experience": "cabinet"},
            {
                "id": "station-revoked", "employer_id": 10,
                "default_experience": "station", "revoked_at": datetime(2026, 10, 13),
            },
        ])
    yield engine, workstations
    engine.dispose()


def test_inventory_is_tenant_scoped_and_reads_revocation(cabinet):
    engine, _ = cabinet
    with engine.connect() as conn:
        result = enrolled_stations_for_tenant(conn, tenant_id=10)
    assert set(result) == {"station-1", "cabinet-desk", "station-revoked"}
    assert result["station-1"].enabled and not result["station-1"].revoked
    assert result["station-revoked"].revoked
    assert not result["station-revoked"].enabled
    assert result["cabinet-desk"].experience == "cabinet"
    assert "station-foreign" not in result


@pytest.mark.parametrize("tenant", [0, -1, "10", True, None])
def test_invalid_tenant_is_denied(cabinet, tenant):
    engine, _ = cabinet
    with engine.connect() as conn:
        with pytest.raises(PrintConfigurationRejected, match="INVALID_TENANT"):
            enrolled_stations_for_tenant(conn, tenant_id=tenant)
        with pytest.raises(PrintConfigurationRejected, match="INVALID_TENANT"):
            independently_certified_printers_for_tenant(conn, tenant_id=tenant)


def test_uncertified_printer_inventory_stays_empty(cabinet):
    engine, _ = cabinet
    with engine.connect() as conn:
        stations = enrolled_stations_for_tenant(conn, tenant_id=10)
        printers = independently_certified_printers_for_tenant(conn, tenant_id=10)
    assert printers == {}
    requested = {
        "schemaVersion": 1, "mode": "reception",
        "stationIds": ["station-1"], "printerIds": ["desk-claimed-by-browser"],
    }
    with pytest.raises(PrintConfigurationRejected, match="PRINTER_NOT_TRUSTED"):
        compile_owner_print_config(
            tenant_id=10, actor_user_id=10, actor_employer_id=None,
            raw=requested, trusted_stations=stations, trusted_printers=printers,
        )


def test_current_inventory_can_save_disabled_without_enabling_print(cabinet):
    engine, _ = cabinet
    with engine.connect() as conn:
        stations = enrolled_stations_for_tenant(conn, tenant_id=10)
        printers = independently_certified_printers_for_tenant(conn, tenant_id=10)
    new_revision = save_owner_configuration(
        engine, tenant_id=10, actor_user_id=10, actor_employer_id=None,
        expected_revision=0,
        proposal={"schemaVersion": 1, "mode": "disabled", "stationIds": [], "printerIds": []},
        trusted_stations=stations, trusted_printers=printers,
    )
    assert new_revision == 1
    loaded = load_effective_configuration(
        engine, tenant_id=10, trusted_stations=stations, trusted_printers=printers,
    )
    assert loaded.policy.mode == "disabled" and not loaded.enabled


def test_station_revocation_is_reflected_without_cache(cabinet):
    engine, workstations = cabinet
    with engine.connect() as conn:
        before = enrolled_stations_for_tenant(conn, tenant_id=10)
    assert before["station-1"].enabled
    with engine.begin() as conn:
        conn.execute(update(workstations).where(workstations.c.id == "station-1").values(
            revoked_at=datetime(2026, 10, 13, tzinfo=timezone.utc),
        ))
    with engine.connect() as conn:
        after = enrolled_stations_for_tenant(conn, tenant_id=10)
    assert after["station-1"].revoked and not after["station-1"].enabled


def test_missing_authoritative_schema_propagates_not_fallback():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.connect() as conn:
        with pytest.raises(OperationalError):
            enrolled_stations_for_tenant(conn, tenant_id=10)
    engine.dispose()
