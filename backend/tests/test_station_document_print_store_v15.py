"""LOT04.8-B2a synthetic SQLAlchemy tests (never touch Cabinet DB)."""
from dataclasses import replace

import pytest
from sqlalchemy import create_engine, insert, select
from sqlalchemy.exc import OperationalError

from backend.services.station_document_print_configuration import (
    PrintConfigurationRejected, TrustedPrinter, TrustedStation,
)
from backend.services.station_document_print_store import (
    PrintConfigurationConflict, audit, configuration, load_effective_configuration,
    printers, save_owner_configuration, schema, stations,
)


@pytest.fixture
def lab():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    schema.create_all(engine)  # TEST ONLY; store has no production DDL.
    inventory_stations = {
        "station-1": TrustedStation("station-1", 1, "station"),
        "station-2": TrustedStation("station-2", 2, "station"),
    }
    inventory_printers = {
        "desk-1": TrustedPrinter(
            "desk-1", 1, "reception", enabled=True, staff_supervised=True,
        ),
        "near-1": TrustedPrinter(
            "near-1", 1, "near_station", station_id="station-1",
            enabled=True, secure_release_verified=True,
            private_channel_verified=True,
        ),
        "desk-2": TrustedPrinter(
            "desk-2", 2, "reception", enabled=True, staff_supervised=True,
        ),
    }
    yield engine, inventory_stations, inventory_printers
    engine.dispose()


def proposal(mode="disabled", stations=(), printers=()):
    return {
        "schemaVersion": 1, "mode": mode,
        "stationIds": list(stations), "printerIds": list(printers),
    }


def save(lab, raw=None, tenant=1, expected=0, actor=None, employer=None):
    engine, trusted_stations, trusted_printers = lab
    return save_owner_configuration(
        engine, tenant_id=tenant,
        actor_user_id=tenant if actor is None else actor,
        actor_employer_id=employer, expected_revision=expected,
        proposal=proposal() if raw is None else raw,
        trusted_stations=trusted_stations, trusted_printers=trusted_printers,
    )


def load(lab, tenant=1, stations_inventory=None, printers_inventory=None):
    engine, trusted_stations, trusted_printers = lab
    return load_effective_configuration(
        engine, tenant_id=tenant,
        trusted_stations=stations_inventory if stations_inventory is not None else trusted_stations,
        trusted_printers=printers_inventory if printers_inventory is not None else trusted_printers,
    )


def db_counts(engine, tenant=1):
    with engine.connect() as connection:
        return tuple(
            len(connection.execute(
                select(table).where(table.c.tenant_id == tenant)
            ).all())
            for table in (configuration, stations, printers, audit)
        )


def test_missing_config_denies_and_has_zero_revision(lab):
    loaded = load(lab)
    assert (loaded.reason, loaded.revision, loaded.enabled) == ("not_configured", 0, False)
    assert loaded.policy.mode == "disabled"
    assert db_counts(lab[0]) == (0, 0, 0, 0)


def test_atomic_first_save_and_effective_owner_reception(lab):
    assert save(lab, proposal("reception", ["station-1"], ["desk-1"])) == 1
    loaded = load(lab)
    assert (loaded.reason, loaded.revision, loaded.enabled) == ("eligible", 1, True)
    assert loaded.policy.mode == "reception"
    assert loaded.policy.allowed_stations == ("station-1",)
    assert loaded.policy.printers[0].printer_id == "desk-1"
    assert db_counts(lab[0]) == (1, 1, 1, 1)


def test_optimistic_lock_rejects_stale_revision_without_audit(lab):
    save(lab, proposal("reception", ["station-1"], ["desk-1"]))
    with pytest.raises(PrintConfigurationConflict, match="STALE_REVISION"):
        save(lab, proposal(), expected=0)
    assert load(lab).policy.mode == "reception"
    assert db_counts(lab[0]) == (1, 1, 1, 1)


@pytest.mark.parametrize("bad", [-1, True, "1", None])
def test_revision_input_is_strict(lab, bad):
    with pytest.raises(PrintConfigurationRejected, match="INVALID_EXPECTED_REVISION"):
        save(lab, proposal(), expected=bad)
    assert db_counts(lab[0]) == (0, 0, 0, 0)


def test_disabled_second_revision_erases_targets_atomically(lab):
    assert save(lab, proposal("both", ["station-1"], ["near-1", "desk-1"])) == 1
    assert save(lab, proposal(), expected=1) == 2
    loaded = load(lab)
    assert loaded.policy.mode == "disabled"
    assert loaded.revision == 2
    assert loaded.reason == "printing_disabled"
    assert db_counts(lab[0]) == (1, 0, 0, 2)


def test_tenants_are_strictly_separated(lab):
    save(lab, proposal("reception", ["station-1"], ["desk-1"]))
    assert save(lab, proposal("reception", ["station-2"], ["desk-2"]), tenant=2) == 1
    assert load(lab, tenant=2).policy.printers[0].printer_id == "desk-2"
    assert load(lab, tenant=1).policy.printers[0].printer_id == "desk-1"
    assert db_counts(lab[0], tenant=2) == (1, 1, 1, 1)


def test_cross_tenant_printer_is_rejected_without_write(lab):
    with pytest.raises(PrintConfigurationRejected):
        save(lab, proposal("reception", ["station-1"], ["desk-2"]))
    assert db_counts(lab[0]) == (0, 0, 0, 0)


@pytest.mark.parametrize("bad", [
    {"tenantId": 2},
    {"secureReleaseVerified": True},
    {"pdfBytes": "%PDF-1.7"},
])
def test_client_supplied_authority_or_bytes_rejected_before_db(lab, bad):
    with pytest.raises(PrintConfigurationRejected, match="INVALID_SCHEMA"):
        save(lab, {**proposal(), **bad})
    assert db_counts(lab[0]) == (0, 0, 0, 0)


def test_unprivileged_staff_cannot_save_even_with_settings_capability(lab):
    with pytest.raises(PrintConfigurationRejected, match="OWNER_REQUIRED"):
        save(lab, proposal(), actor=20, employer=1)
    assert db_counts(lab[0]) == (0, 0, 0, 0)


def test_inventory_revocation_after_save_disables_effective_policy(lab):
    save(lab, proposal("near_station", ["station-1"], ["near-1"]))
    stations_inventory = dict(lab[1], **{"station-1": replace(lab[1]["station-1"], revoked=True)})
    loaded = load(lab, stations_inventory=stations_inventory)
    assert (loaded.policy.mode, loaded.reason, loaded.enabled) == (
        "disabled", "inventory_changed", False,
    )
    assert db_counts(lab[0]) == (1, 1, 1, 1)


def test_printer_certification_loss_after_save_denies(lab):
    save(lab, proposal("both", ["station-1"], ["near-1", "desk-1"]))
    printers_inventory = dict(lab[2], **{
        "near-1": replace(lab[2]["near-1"], private_channel_verified=False)
    })
    assert load(lab, printers_inventory=printers_inventory).policy.mode == "disabled"


def test_missing_printer_inventory_denies_without_downgrade(lab):
    save(lab, proposal("both", ["station-1"], ["near-1", "desk-1"]))
    inventories = {"desk-1": lab[2]["desk-1"]}
    result = load(lab, printers_inventory=inventories)
    assert (result.policy.mode, result.enabled) == ("disabled", False)


def test_invalid_stored_disabled_config_is_not_accepted(lab):
    save(lab, proposal())
    with lab[0].begin() as connection:
        connection.execute(insert(stations).values(tenant_id=1, station_id="station-1"))
    loaded = load(lab)
    assert loaded.reason == "configuration_invalid"
    assert loaded.policy.mode == "disabled"


def test_two_cabinet_revisions_have_exactly_two_minimal_audit_events(lab):
    save(lab, proposal("reception", ["station-1"], ["desk-1"]))
    save(lab, proposal(), expected=1)
    with lab[0].connect() as connection:
        entries = connection.execute(
            select(audit.c.tenant_id, audit.c.revision, audit.c.actor_user_id, audit.c.mode)
        ).all()
        assert entries == [(1, 1, 1, "reception"), (1, 2, 1, "disabled")]
        assert not any(column.name in {"patient_id", "pdf", "token", "qr_code", "pin"} for column in audit.columns)


def test_failure_of_audit_insert_rolls_back_configuration(lab):
    # Recreate the schema from scratch in this isolated lab without audit.
    with lab[0].begin() as connection:
        audit.drop(connection)
    with pytest.raises(OperationalError):
        save(lab, proposal("reception", ["station-1"], ["desk-1"]))
    with lab[0].connect() as connection:
        assert connection.execute(select(configuration.c.tenant_id)).all() == []
        assert connection.execute(select(stations.c.station_id)).all() == []
        assert connection.execute(select(printers.c.printer_id)).all() == []


def test_expected_nonzero_revision_requires_existing_record(lab):
    with pytest.raises(PrintConfigurationConflict, match="STALE_REVISION"):
        save(lab, proposal(), expected=4)
    assert db_counts(lab[0]) == (0, 0, 0, 0)
