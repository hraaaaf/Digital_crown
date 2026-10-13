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
