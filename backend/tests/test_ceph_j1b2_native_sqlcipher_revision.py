"""J1.B2 Windows FUE: encrypted scientific CAS, full reread and isolated restore.

Synthetic SQLCipher bytes only. This does NOT create an installer or access a
cabinet database, imaging media, network or a real patient record.
"""
from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
import secrets
import shutil
import sys

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["DIGITALCROWN_ISOLATED_RUNTIME"] = "true"
os.environ["CABINET_MASTER_KEY_HEX"] = "00" * 32

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_clinical_cas import STAGING_KEY, R14_KEY
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.cephalo_scientific_write import save_scientific_transition
from backend.tests.test_cephalo_p2ter_windows_sqlcipher_native import (
    _check_encrypted,
    _make_engine,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Native Windows SQLCipher only")

PATIENT_ID = 812345
STUDY_ID = 812346
CASE = "case:synthetic-j1b2-desktop"


def _graph(revision: int, *, x: float) -> dict:
    current = "landmark:synthetic-j1b2:r2:A"
    original = "landmark:synthetic-j1b2:r1:A"
    auto = {
        "evidence_id": original,
        "landmark_id": "A",
        "origin": "SRPOSE38_AUTO",
        "x": 100.0,
        "y": 120.0,
    }
    manual = {
        "evidence_id": current,
        "landmark_id": "A",
        "origin": "MANUAL_CORRECTED",
        "x": x,
        "y": 120.0,
        "original_auto_x": 100.0,
        "original_auto_y": 120.0,
        "validated_by": "synthetic-clinician-42",
    }
    return {
        "schema_version": "CEPHALO_EVIDENCE_V1",
        "case_id": CASE,
        "revision": revision,
        "sources": [{"synthetic_only": True}],
        "landmarks": [auto] if revision == 1 else [auto, manual],
        "current_landmark_refs": [original if revision == 1 else current],
        "history": [] if revision == 1 else [{"revision": 1, "synthetic_only": True}],
    }


def _stored(engine):
    with Session(engine) as db:
        a = db.get(models.CephaloAnalysis, STUDY_ID)
        assert a is not None and a.patient_id == PATIENT_ID
        return copy.deepcopy(a.angles_data), copy.deepcopy(a.landmarks_data)


def test_windows_sqlcipher_scientific_revision_reopen_restore_and_stale_cas(tmp_path: Path):
    assert str(tmp_path.resolve()).lower().find("appdata\\roaming\\digitalcrown") == -1
    path = tmp_path / "synthetic-ceph-j1b2-sqlcipher.db"
    backup = tmp_path / "synthetic-ceph-j1b2-restore.db"
    key = secrets.token_hex(32)
    engine = _make_engine(path, key)
    try:
        models.CephaloAnalysis.__table__.create(engine, checkfirst=True)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
            assert str(c.exec_driver_sql("PRAGMA journal_mode=WAL").scalar()).lower() == "wal"
        _check_encrypted(engine, path)

        original = {
            EVIDENCE_GRAPH_KEY: _graph(1, x=100.0),
            STAGING_KEY: {"content_sha256": "a" * 64},
            R14_KEY: {"content_sha256": "b" * 64},
            "metrics": {"SNA": 81},
        }
        with Session(engine) as db:
            db.add(models.CephaloAnalysis(
                id=STUDY_ID,
                patient_id=PATIENT_ID,
                image_original_path="synthetic://no-real-radiograph",
                landmarks_data=[{"id": "A", "x": 100.0, "y": 120.0}],
                angles_data=original,
            ))
            db.commit()

        # Two independently loaded sessions must never both write the same
        # scientific revision. The loser cannot overwrite the clinician receipt.
        with Session(engine) as stale:
            first = stale.get(models.CephaloAnalysis, STUDY_ID)
            assert first.angles_data[EVIDENCE_GRAPH_KEY]["revision"] == 1
            with Session(engine) as winner:
                a = winner.get(models.CephaloAnalysis, STUDY_ID)
                save_scientific_transition(
                    db=winner, analysis=a,
                    updated_angles={
                        EVIDENCE_GRAPH_KEY: _graph(2, x=105.0),
                        "metrics": {"SNA": 82},
                        # A forged UI-supplied receipt is never persisted.
                        R14_KEY: {"content_sha256": "f" * 64},
                    },
                    other_values={
                        "landmarks_data": [{"id": "A", "x": 105.0, "y": 120.0}],
                    },
                )
                winner.commit()
            with pytest.raises(HTTPException) as conflict:
                save_scientific_transition(
                    db=stale, analysis=first,
                    updated_angles={EVIDENCE_GRAPH_KEY: _graph(2, x=999.0)},
                )
            assert conflict.value.status_code == 409

        before, points = _stored(engine)
        assert before[EVIDENCE_GRAPH_KEY]["revision"] == 2
        assert before[EVIDENCE_GRAPH_KEY]["landmarks"][-1]["validated_by"] == "synthetic-clinician-42"
        assert before[EVIDENCE_GRAPH_KEY]["landmarks"][-1]["original_auto_x"] == 100.0
        assert before[EVIDENCE_GRAPH_KEY]["current_landmark_refs"] == ["landmark:synthetic-j1b2:r2:A"]
        assert before[STAGING_KEY]["content_sha256"] == "a" * 64
        assert before[R14_KEY]["content_sha256"] == "b" * 64
        assert points == [{"id": "A", "x": 105.0, "y": 120.0}]
        _check_encrypted(engine, path)
    finally:
        engine.dispose()

    # Explicit WAL checkpoint before copying the encrypted DB, never copy
    # uncheckpointed WAL alone and call it a complete backup.
    checkpoint_engine = _make_engine(path, key)
    try:
        with checkpoint_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as c:
            checkpoint = tuple(c.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)").first())
            assert checkpoint[0] == 0, "SQLCipher checkpoint was busy"
    finally:
        checkpoint_engine.dispose()

    shutil.copy2(path, backup)
    assert path.read_bytes()[:16] != b"SQLite format 3\\x00"
    assert hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(backup.read_bytes()).digest()

    reopened = _make_engine(path, key)
    restored = _make_engine(backup, key)
    try:
        _check_encrypted(reopened, path)
        _check_encrypted(restored, backup)
        assert _stored(reopened) == (before, points)
        assert _stored(restored) == (before, points)
    finally:
        reopened.dispose()
        restored.dispose()
    print("J1B2_WINDOWS_SQLCIPHER_RESTORE_PASS revisions=2 cas=409 plaintext_read=denied")
