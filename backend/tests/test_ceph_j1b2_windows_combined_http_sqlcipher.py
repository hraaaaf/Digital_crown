"""J1.B2 FUE-I Windows: SAME real API/JWT path and native encrypted DB.

The FastAPI TestClient serves real JWT endpoints against a disposable
SQLCipher file. Then WAL is checkpointed and the encrypted copy is mounted
back into that same application for authenticated HTTP reread. No model
inference, patient content, production data, release or installer.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import secrets
import shutil
import sys

import pytest
from sqlalchemy.orm import Session, sessionmaker

from backend import database, models
from backend.routers import auth
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.tests.conftest import make_user
from backend.tests.p2ter_bridge_synthetic_support import _case, _jwt
from backend.tests.test_cephalo_p2ter_windows_sqlcipher_native import (
    _check_encrypted,
    _make_engine,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native Windows SQLCipher only")


def _mount_real_api_on_engine(app, engine, monkeypatch):
    """Route HTTP dependencies AND non-Depends license lookup to one vault.

    SessionLocal is also used by main._get_user_status_sync() for the
    fail-closed local license gate, outside FastAPI dependency injection.
    Merely overriding get_db would create a false USER_NOT_FOUND and would
    not prove a real authenticated Desktop-to-SQLCipher flow.
    """
    sqlcipher_sessionmaker = sessionmaker(
        bind=engine, autocommit=False, autoflush=False
    )
    monkeypatch.setattr(database, "SessionLocal", sqlcipher_sessionmaker)

    def sqlcipher_db():
        with sqlcipher_sessionmaker() as session:
            yield session

    # All API routes plus the out-of-band license lookup must read the
    # same encrypted synthetic vault. Never bypass license checking.
    assert app.dependency_overrides, "Real TestClient DB overrides not initialized"
    for source in tuple(app.dependency_overrides):
        app.dependency_overrides[source] = sqlcipher_db
    app.dependency_overrides[database.get_db] = sqlcipher_db
    app.dependency_overrides[auth.get_db] = sqlcipher_db


def _snapshot(engine, study_id):
    with Session(engine) as session:
        row = session.get(models.CephaloAnalysis, study_id)
        assert row is not None
        return copy.deepcopy(row.angles_data[EVIDENCE_GRAPH_KEY])


def test_native_windows_one_process_jwt_edit_encrypted_restore_and_reread(
    client, tmp_path: Path, monkeypatch,
):
    from backend.main import app

    vault = tmp_path / "J1B2_TEST_ONLY_native_encrypted.db"
    restored_path = tmp_path / "J1B2_TEST_ONLY_restored.db"
    key = secrets.token_hex(32)
    engine = _make_engine(vault, key)
    study_id = None
    owner_headers = None
    foreign_headers = None
    revision2 = None
    try:
        # No patient files, device paths, cached workstation profile or original media.
        assert str(vault.resolve()).lower().find("appdata\\roaming\\digitalcrown") == -1
        models.Base.metadata.create_all(bind=engine)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            assert str(conn.exec_driver_sql("PRAGMA journal_mode=WAL").scalar()).lower() == "wal"
        _check_encrypted(engine, vault)

        _mount_real_api_on_engine(app, engine, monkeypatch)
        with Session(engine) as session:
            owner = make_user(session)
            patient, study, original = _case(session, owner)
            study_id = study.id
            owner_id = owner.id
            foreign = make_user(session)
            foreign_id = foreign.id
            patient_id = patient.id
            # Keep only primitive values after the SQLAlchemy seed session closes.
            owner_email = owner.email
            foreign_email = foreign.email

        from types import SimpleNamespace
        owner_headers = _jwt(client, SimpleNamespace(email=owner_email))
        foreign_headers = _jwt(client, SimpleNamespace(email=foreign_email))
        url = "/api/ia/analyses/" + str(study_id)
        modified = [dict(p) for p in original]
        pt = next(p for p in modified if p["id"] == "A")
        original_x = pt["x"]
        pt["x"] += 5.0
        incoming = {
            "landmarks": modified,
            "ai_diagnostic": {
                "validated_by": str(foreign_id),
                "clinician_id": "forged-windows-operator",
            },
        }

        assert client.put(url, json=incoming).status_code == 401
        assert client.put(url, json=incoming, headers=foreign_headers).status_code == 403
        assert client.get(url, headers=foreign_headers).status_code == 403
        assert _snapshot(engine, study_id)["revision"] == 1

        accepted = client.put(url, json=incoming, headers=owner_headers)
        assert accepted.status_code == 200, accepted.text[:750]
        revision2 = _snapshot(engine, study_id)
        assert revision2["revision"] == 2
        assert revision2["revision_reason"] == "LANDMARK_EDIT"
        active = set(revision2["current_landmark_refs"])
        manual = [
            x for x in revision2["landmarks"]
            if x["landmark_id"] == "A" and x["evidence_id"] in active
        ]
        assert len(manual) == 1
        assert manual[0]["validated_by"] == str(owner_id)
        assert manual[0]["validated_by"] != str(foreign_id)
        assert manual[0]["original_auto_x"] == original_x
        assert manual[0]["x"] == original_x + 5.0
        assert manual[0]["origin"] == "MANUAL_CORRECTED"
        assert all(
            x["origin"] == "SRPOSE38_AUTO"
            for x in revision2["landmarks"]
            if x["landmark_id"] == "Co" and x["evidence_id"] in active
        )
        assert patient_id is not None
        _check_encrypted(engine, vault)

        # Finalize all HTTP sessions and checkpoint before any byte-copy.
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            checkpoint = tuple(conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)").first())
            assert checkpoint[0] == 0
    finally:
        engine.dispose()

    shutil.copy2(vault, restored_path)
    assert not vault.read_bytes().startswith(b"SQLite format 3")
    assert vault.read_bytes() == restored_path.read_bytes()
    assert hashlib.sha256(vault.read_bytes()).digest() == hashlib.sha256(restored_path.read_bytes()).digest()

    restored_engine = _make_engine(restored_path, key)
    try:
        _check_encrypted(restored_engine, restored_path)
        assert _snapshot(restored_engine, study_id) == revision2
        _mount_real_api_on_engine(app, restored_engine, monkeypatch)
        # Do not reuse a positive license decision from the pre-backup DB.
        # A restored cabinet must independently re-establish local user status.
        from backend import main as main_module
        main_module._license_cache.clear()

        url = "/api/ia/analyses/" + str(study_id)
        denied = client.get(url, headers=foreign_headers)
        assert denied.status_code == 403, denied.text[:500]
        reread = client.get(url, headers=owner_headers)
        assert reread.status_code == 200, reread.text[:750]
        assert reread.json()["angles_data"][EVIDENCE_GRAPH_KEY] == revision2

        replay = client.put(
            url, json={"landmarks": modified}, headers=owner_headers,
        )
        assert replay.status_code == 200, replay.text[:750]
        assert _snapshot(restored_engine, study_id) == revision2
    finally:
        restored_engine.dispose()
    print("J1B2_WINDOWS_JWT_SQLCIPHER_ONE_PROCESS_PASS 401=denied 403=denied revision=2 encrypted_restore=verified")
