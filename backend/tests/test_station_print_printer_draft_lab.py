"""Printer inventory LAB tests: proposals are never hardware attestations."""
from dataclasses import replace

import pytest
from sqlalchemy import create_engine, select

from backend.services.station_print_printer_draft_lab import (
    SCHEMA, draft_printers, PrinterDraftConflict, PrinterDraftRejected,
    list_unverified_drafts, register_unverified_draft,
    unverified_drafts_are_never_trusted,
)
from backend.services.station_document_print_configuration import (
    PrintConfigurationRejected, compile_owner_print_config,
)


@pytest.fixture
def engine():
    db = create_engine("sqlite+pysqlite:///:memory:")
    SCHEMA.create_all(db)  # Lab-only, never production!
    yield db
    db.dispose()


def save(engine, *, tenant=10, actor=10, employer=None, printer="desk1",
         location="reception", station=None, revision=0):
    return register_unverified_draft(
        engine, tenant_id=tenant, actor_user_id=actor,
        actor_employer_id=employer, printer_id=printer,
        location=location, station_id=station, expected_revision=revision,
    )


def test_defaults_disabled_and_owner_only(engine):
    assert save(engine) == 1
    records = list_unverified_drafts(engine, tenant_id=10)
    assert len(records) == 1
    assert records[0].revision == 1
    assert records[0].certification == "unverified"
    assert not records[0].enabled


@pytest.mark.parametrize("actor,employer,tenant", [
    (11, None, 10), (10, 10, 10), (11, 10, 10),
    (True, None, 10), (10, None, 20), (10, None, -1),
])
def test_no_delegated_or_other_tenant_owners(engine, actor, employer, tenant):
    with pytest.raises(PrinterDraftRejected, match="OWNER_REQUIRED"):
        save(engine, actor=actor, employer=employer, tenant=tenant)
    assert list_unverified_drafts(engine, tenant_id=10) == ()


@pytest.mark.parametrize("kwargs", [
    {"printer": ""}, {"printer": "desk/../../etc"}, {"printer": "a" * 81},
    {"location": "both"}, {"location": ["reception"]},
    {"location": "near_station"}, {"location": "reception", "station": "station1"},
    {"location": "near_station", "station": "../other"},
])
def test_bad_input_is_denied_before_write(engine, kwargs):
    with pytest.raises(PrinterDraftRejected, match="INVALID_PRINTER_DRAFT"):
        save(engine, **kwargs)
    assert list_unverified_drafts(engine, tenant_id=10) == ()


@pytest.mark.parametrize("revision", [True, -1, "0"])
def test_revision_must_be_strict_integer(engine, revision):
    with pytest.raises(PrinterDraftRejected, match="INVALID_REVISION"):
        save(engine, revision=revision)


def test_cross_tenant_isolation_and_same_printer_id(engine):
    save(engine)
    save(engine, tenant=11, actor=11)
    assert list_unverified_drafts(engine, tenant_id=10)[0].tenant_id == 10
    assert list_unverified_drafts(engine, tenant_id=11)[0].tenant_id == 11


def test_duplicate_and_stale_revision_are_rejected(engine):
    assert save(engine) == 1
    with pytest.raises(PrinterDraftConflict, match="DUPLICATE"):
        save(engine)
    assert save(engine, location="near_station", station="station1", revision=1) == 2
    with pytest.raises(PrinterDraftConflict, match="STALE_REVISION"):
        save(engine, revision=1)
    updated = list_unverified_drafts(engine, tenant_id=10)[0]
    assert (updated.revision, updated.location, updated.station_id) == (
        2, "near_station", "station1",
    )


def test_draft_remains_untrusted_and_cannot_enable_policy(engine):
    save(engine)
    records = list_unverified_drafts(engine, tenant_id=10)
    targets = unverified_drafts_are_never_trusted(records)
    assert targets["desk1"].enabled is False
    assert targets["desk1"].staff_supervised is False
    assert targets["desk1"].secure_release_verified is False
    assert targets["desk1"].private_channel_verified is False
    with pytest.raises(PrintConfigurationRejected):
        compile_owner_print_config(
            tenant_id=10, actor_user_id=10, actor_employer_id=None,
            raw={"schemaVersion": 1, "mode": "reception",
                 "stationIds": ["s1"], "printerIds": ["desk1"]},
            trusted_stations={}, trusted_printers=targets,
        )


def test_registry_does_not_store_a_fake_attestation_or_patient_information(engine):
    names = {col.name for col in draft_printers.columns}
    assert names == {"tenant_id", "printer_id", "location", "station_id",
                     "revision", "updated_by", "updated_at"}
    assert not names.intersection({
        "patient_id", "document_bytes", "secure_release_verified",
        "staff_supervised", "private_channel_verified", "pdf",
    })


def test_database_blocks_invalid_location_even_when_bypassing_service(engine):
    from sqlalchemy import insert
    from sqlalchemy.exc import IntegrityError
    from datetime import datetime, timezone
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(insert(draft_printers).values(
                tenant_id=10, printer_id="bad", location="near_station",
                station_id=None, revision=1, updated_by=10,
                updated_at=datetime.now(timezone.utc),
            ))
    assert list_unverified_drafts(engine, tenant_id=10) == ()
