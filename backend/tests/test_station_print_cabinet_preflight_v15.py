"""04.8-C live-schema-shaped Cabinet preflight: proof of deny-first reads.

Fake identity rows, no PHI, no real data, no Cabinet transaction/print worker.
Unlike a pure mocked permission bool, the service executes real SQL joins,
canonical eligibility evaluation, and archive digest equality checks.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, insert, update

from backend.services.station_print_cabinet_preflight_v15 import (
    inspect_cabinet_care_sheet_preflight,
)

NOW = datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc)
SESSION_ID = "00000000-0000-4000-8000-000000000001"
SHA = "c" * 64


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
    patients = Table(
        "patients", meta,
        Column("id", Integer, primary_key=True),
        Column("employer_id", Integer, nullable=False),
        Column("deleted_at", DateTime()),
    )
    sessions = Table(
        "workstation_patient_sessions", meta,
        Column("id", String(36), primary_key=True),
        Column("employer_id", Integer, nullable=False),
        Column("workstation_id", String(36)),
        Column("patient_id", Integer),
        Column("created_at", DateTime()),
        Column("claimed_at", DateTime()),
        Column("expires_at", DateTime()),
        Column("purged_at", DateTime()),
    )
    docs = Table(
        "document_archives", meta,
        Column("id", Integer, primary_key=True),
        Column("patient_id", Integer),
        Column("file_hash", String(64)),
        Column("file_size", Integer),
        Column("filename", String(64)),
        Column("status", String(16)),
        Column("is_latest_version", Integer),
        Column("deleted_at", DateTime()),
    )
    meta.create_all(engine)
    created = NOW - timedelta(seconds=40)
    claimed = NOW - timedelta(seconds=35)
    expires = NOW + timedelta(seconds=75)
    with engine.begin() as c:
        c.execute(insert(workstations), [
            {"id": "cabinet-10", "employer_id": 10, "default_experience": "cabinet", "revoked_at": None},
            {"id": "station-10", "employer_id": 10, "default_experience": "station", "revoked_at": None},
            {"id": "cabinet-20", "employer_id": 20, "default_experience": "cabinet", "revoked_at": None},
        ])
        c.execute(insert(patients), [
            {"id": 101, "employer_id": 10, "deleted_at": None},
            {"id": 201, "employer_id": 20, "deleted_at": None},
        ])
        c.execute(insert(sessions), [{
            "id": SESSION_ID, "employer_id": 10,
            "workstation_id": "station-10", "patient_id": 101,
            "created_at": created.replace(tzinfo=None),
            "claimed_at": claimed.replace(tzinfo=None),
            "expires_at": expires.replace(tzinfo=None),
            "purged_at": None,
        }])
        c.execute(insert(docs), [{
            "id": 30, "patient_id": 101, "file_hash": SHA, "file_size": 1024,
            "filename": "synthetic.pdf", "status": "ACTIF",
            "is_latest_version": 1, "deleted_at": None,
        }])
    yield engine, (workstations, patients, sessions, docs)
    engine.dispose()


def inspect(engine, **overrides):
    kwargs = dict(
        tenant_id=10, actor_user_id=10, actor_employer_id=None,
        cabinet_workstation_id="cabinet-10", session_id=SESSION_ID,
        document_id=30, expected_archive_sha256=SHA, now=NOW,
    )
    kwargs.update(overrides)
    with engine.connect() as connection:
        return inspect_cabinet_care_sheet_preflight(connection, **kwargs)


def test_valid_structural_source_is_still_not_print_permitted(cabinet):
    engine, _ = cabinet
    result = inspect(engine)
    assert result.allowed is False
    assert result.reason == "FINALIZATION_WITHDRAWAL_POLICY_AND_PHYSICAL_PROOF_REQUIRED"
    assert (result.session_id, result.document_id, result.document_sha256) == (SESSION_ID, 30, SHA)
    assert not hasattr(result, "patient_name")
    assert not hasattr(result, "pdf_bytes")


@pytest.mark.parametrize("override", [
    {"tenant_id": 20, "actor_user_id": 20, "cabinet_workstation_id": "cabinet-20"},
    {"tenant_id": -1, "actor_user_id": -1},
    {"tenant_id": True, "actor_user_id": True},
    {"actor_user_id": 11},
    {"actor_employer_id": 10},
    {"cabinet_workstation_id": "station-10"},
    {"cabinet_workstation_id": "cabinet-20"},
    {"session_id": "00000000-0000-4000-8000-000000000999"},
    {"session_id": "X"},
    {"document_id": 31},
    {"document_id": True},
    {"expected_archive_sha256": "0" * 64},
    {"expected_archive_sha256": "c" * 63},
])
def test_wrong_identity_selector_and_wrong_archive_sha_denied(cabinet, override):
    engine, _ = cabinet
    result = inspect(engine, **override)
    assert not result.allowed
    assert result.reason != "FINALIZATION_WITHDRAWAL_POLICY_AND_PHYSICAL_PROOF_REQUIRED"


@pytest.mark.parametrize("table_index,where_column,where_value,change", [
    (0, "id", "cabinet-10", {"revoked_at": NOW.replace(tzinfo=None)}),
    (0, "id", "station-10", {"revoked_at": NOW.replace(tzinfo=None)}),
    (0, "id", "station-10", {"default_experience": "cabinet"}),
    (0, "id", "station-10", {"employer_id": 20}),
    (1, "id", 101, {"employer_id": 20}),
    (1, "id", 101, {"deleted_at": NOW.replace(tzinfo=None)}),
    (2, "id", SESSION_ID, {"claimed_at": None}),
    (2, "id", SESSION_ID, {"purged_at": NOW.replace(tzinfo=None)}),
    (2, "id", SESSION_ID, {"expires_at": NOW.replace(tzinfo=None)}),
    (2, "id", SESSION_ID, {"created_at": (NOW - timedelta(minutes=5)).replace(tzinfo=None)}),
    (2, "id", SESSION_ID, {"patient_id": 201}),
    (3, "id", 30, {"patient_id": 201}),
    (3, "id", 30, {"status": "ARCHIVED"}),
    (3, "id", 30, {"is_latest_version": 0}),
    (3, "id", 30, {"deleted_at": NOW.replace(tzinfo=None)}),
    (3, "id", 30, {"file_hash": "d" * 64}),
    (3, "id", 30, {"file_size": 0}),
    (3, "id", 30, {"filename": "fake.txt"}),
])
def test_revoked_expired_foreign_or_stale_db_facts_denied(
    cabinet, table_index, where_column, where_value, change,
):
    engine, tables = cabinet
    table = tables[table_index]
    with engine.begin() as connection:
        connection.execute(
            update(table).where(table.c[where_column] == where_value).values(**change)
        )
    result = inspect(engine)
    assert result.allowed is False
    assert result.reason != "FINALIZATION_WITHDRAWAL_POLICY_AND_PHYSICAL_PROOF_REQUIRED"


def test_db_errors_do_not_fall_back_to_client_proofs():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.connect() as connection:
        from sqlalchemy.exc import OperationalError
        with pytest.raises(OperationalError):
            inspect_cabinet_care_sheet_preflight(
                connection, tenant_id=10, actor_user_id=10, actor_employer_id=None,
                cabinet_workstation_id="cabinet-10", session_id=SESSION_ID,
                document_id=30, expected_archive_sha256=SHA, now=NOW,
            )
    engine.dispose()


def test_cabinet_clinical_gate_reuses_real_sql_and_denies_without_certification(cabinet, monkeypatch):
    """Actual SQL ORM queries; ONLY clinical audit/file reader are test stubs.

    Real care_sheet_state / verified_care_sheet_bytes have separate 04.3 tests.
    The LAB mock cannot grant any print claim or authorize a Station route.
    """
    import hashlib
    import importlib
    import sys
    import types
    from sqlalchemy.orm import Session, registry

    engine, tables = cabinet
    payload = b"%PDF-1.4\n% synthetic only\n%%EOF\n"
    digest = hashlib.sha256(payload).hexdigest()
    with engine.begin() as conn:
        conn.execute(update(tables[3]).where(tables[3].c.id == 30).values(
            file_hash=digest, file_size=len(payload),
        ))
    mapping = registry()
    class FakeStationSession: pass
    class FakeDocumentArchive: pass
    mapping.map_imperatively(FakeStationSession, tables[2])
    mapping.map_imperatively(FakeDocumentArchive, tables[3])

    models = types.ModuleType("backend.models")
    models.WorkstationPatientSession = FakeStationSession
    models.DocumentArchive = FakeDocumentArchive
    models.DocumentStatus = types.SimpleNamespace(ACTIF="ACTIF")
    care = types.ModuleType("backend.services.station_care_sheet")
    audit = {"finalized": True, "withdrawal": True, "bytes": payload, "reads": 0}
    care.care_sheet_state = lambda *args, **kwargs: types.SimpleNamespace(
        finalized=audit["finalized"], withdrawal_authorized=audit["withdrawal"],
    )
    def read_verified_bytes(document):
        audit["reads"] += 1
        return audit["bytes"]
    care.verified_care_sheet_bytes = read_verified_bytes

    monkeypatch.setitem(sys.modules, "backend.models", models)
    monkeypatch.setitem(sys.modules, "backend.services.station_care_sheet", care)
    monkeypatch.delitem(sys.modules, "backend.services.station_print_cabinet_clinical_gate_v15", raising=False)
    module = importlib.import_module("backend.services.station_print_cabinet_clinical_gate_v15")
    user = types.SimpleNamespace(id=10, employer_id=None)
    workstation = types.SimpleNamespace(
        id="cabinet-10", employer_id=10,
        revoked_at=None, default_experience="cabinet",
    )

    def check(**overrides):
        kwargs = dict(
            authenticated_user=user, authenticated_workstation=workstation,
            session_id=SESSION_ID, document_id=30,
            expected_sha256=digest, now=NOW,
        )
        kwargs.update(overrides)
        with Session(engine) as db:
            result = module.clinically_recheck_cabinet_print(db, **kwargs)
            assert db.in_transaction()
            db.rollback()
        assert result.allowed is False
        return result

    assert check().reason == "TRUSTED_PRINTER_CERTIFICATION_REQUIRED"
    assert audit["reads"] == 1
    audit["withdrawal"] = False
    assert check().reason == "WITHDRAWAL_NOT_AUTHORIZED"
    audit["finalized"] = False
    assert check().reason == "CARE_SHEET_NOT_FINALIZED"
    assert audit["reads"] == 1

    audit["finalized"] = audit["withdrawal"] = True
    audit["bytes"] = b"%PDF-1.4\n% not the expected bytes\n%%EOF"
    assert check().reason == "ARCHIVE_DIGEST_CHANGED"
    assert check(authenticated_user=types.SimpleNamespace(
        id=11, employer_id=10,
    )).reason == "CABINET_OWNER_WORKSTATION_REQUIRED"
    assert check(authenticated_workstation=types.SimpleNamespace(
        id="station-10", employer_id=10, revoked_at=None,
        default_experience="station",
    )).reason == "CABINET_OWNER_WORKSTATION_REQUIRED"
    assert check(session_id="00000000-0000-4000-8000-000000000999").reason == "SESSION_NOT_AVAILABLE"
    monkeypatch.delitem(sys.modules, "backend.services.station_print_cabinet_clinical_gate_v15", raising=False)
