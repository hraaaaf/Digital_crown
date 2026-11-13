"""J5 independent adversarial review of approved descriptive A4 archive.

Exercises two actual SQLite connections, scientific revision writer lock, a
single authoritative archive row and the existing recovery journal with the
S2B identity/digest. No patient data, clinical activation, or cloud calls.
The full real-JWT/typed-science route remains covered separately by S2B E2E.
"""
from __future__ import annotations

import base64
import hashlib
import threading
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend import models
from backend.routers import patients
from backend.services import archive_service
from backend.services import cephalo_a4_approval_v1 as approval
from backend.services.cephalo_archive_recovery import prepare_official_pdf
from backend.services.cephalo_document_lock import verified_official_archive_bytes


def _practitioner():
    return SimpleNamespace(
        id=44, role=models.UserRole.DENTISTE, nom_complet="Dr. Test J5", is_active=True,
        approval_status=models.ApprovalStatus.APPROVED.value,
        get_employer_id=lambda: 44,
    )


def _pdf(n: int) -> bytes:
    return b"%PDF-1.4\n%SYNTHETIC-J5-APPROVAL-" + str(n).encode() + b"\n%%EOF\n"


def _source(engine):
    with Session(engine) as db:
        return approval.scientific_fingerprint(db.get(models.CephaloAnalysis, 9001))


def _payload(engine, *, pdf: bytes, issued=None):
    actor = _practitioner()
    sha = hashlib.sha256(pdf).hexdigest()
    with Session(engine) as db:
        rendered_identity_sha256 = approval.rendered_identity_fingerprint(
            patient=db.get(models.Patient, 8001),
            cabinet=db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == 44).one(),
            user=actor,
        )
    token = approval.make_approval_token(
        user=actor, patient_id=8001, analysis_id=9001,
        revision=3, source_sha256=_source(engine),
        rendered_identity_sha256=rendered_identity_sha256,
        pdf_sha256=sha, pdf_length=len(pdf), now=issued,
    )
    return patients.CephaloA4ArchiveV1(
        analysis_id=9001, expected_revision=3,
        pdf_base64=base64.b64encode(pdf).decode(),
        approval_token=token, approved=True,
    )


@pytest.fixture()
def s2b_sqlite(tmp_path, monkeypatch):
    db_file = tmp_path / "s2b-j5-real-file.sqlite"
    engine = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 10},
    )
    # P3 provenance is attached by global pytest conftest before schema create.
    for table in (
        models.Patient.__table__, models.CabinetConfig.__table__,
        models.CephaloAnalysis.__table__, models.DocumentArchive.__table__,
        models.AuditLog.__table__,
    ):
        table.create(engine)
    with Session(engine) as db:
        db.add(models.Patient(
            id=8001, employer_id=44, nom="SYNTHETIC-J5",
            prenom="NEVER-REAL", date_naissance=datetime(1990, 1, 1),
            sexe="M",
        ))
        db.add(models.CabinetConfig(
            owner_id=44, nom_cabinet="SYNTHETIC J5 CABINET",
            nom_praticien="Dr. Test J5",
        ))
        db.add(models.CephaloAnalysis(
            id=9001, patient_id=8001,
            image_original_path="synthetic://j5/test.jpeg",
            angles_data={"scientific_revision": 3, "synthetic": True},
            landmarks_data=[{"id": "S", "x": 1, "y": 2}],
            is_calibrated=True, mm_per_pixel=0.2,
        ))
        db.commit()
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archive-root")
    monkeypatch.setattr(archive_service, "MEDIA_DIR", tmp_path)
    monkeypatch.setattr(archive_service, "LEGACY_DOCS_DIR", tmp_path / "documents")
    # Isolate concurrency/archiving layer from typed-science fixture; the
    # authenticated clinical-safety typed gate is tested in the S2B JWT E2E.
    def bound(patient_id, analysis_id, expected_revision, db, current_user):
        if patient_id != 8001 or analysis_id != 9001 or expected_revision != 3:
            raise HTTPException(status_code=409, detail="Etude incorrecte")
        study = db.get(models.CephaloAnalysis, 9001)
        if study is None or study.patient_id != patient_id:
            raise HTTPException(status_code=404, detail="Etude absente")
        return study, 3
    monkeypatch.setattr(patients, "_bound_cephalo_study", bound)
    monkeypatch.setattr(approval, "require_descriptive_science", lambda *args, **kwargs: None)
    yield engine, tmp_path / "archive-root"
    engine.dispose()


def _run_route(engine, payload):
    with Session(engine) as db:
        try:
            result = patients.archive_descriptive_cephalo_a4_v1(
                8001, payload, db=db, current_user=_practitioner()
            )
            return result.status_code, result.headers, result.body
        except HTTPException as exc:
            db.rollback()
            return exc.status_code, {}, b""
        except BaseException:
            db.rollback()
            raise


@pytest.mark.parametrize("different_pdf", [False, True])
def test_two_real_connections_serialize_and_cannot_fork_approved_archive(
    s2b_sqlite, monkeypatch, different_pdf,
):
    from backend.services import cephalo_document_lock

    engine, root = s2b_sqlite
    original = _pdf(1)
    a = _payload(engine, pdf=original)
    b = _payload(engine, pdf=_pdf(2) if different_pdf else original)
    entered = threading.Event()
    release = threading.Event()
    second_started = threading.Event()
    completed = []
    true_lock = cephalo_document_lock.lock_selected_cephalo_for_archive
    # The route imported the lock function into its module; this wrapper does
    # not replace the actual SQLite writer lock.
    def delayed(db, *, patient_id, analysis_id):
        true_lock(db, patient_id=patient_id, analysis_id=analysis_id)
        if threading.current_thread().name == "first_s2b_archive":
            entered.set()
            assert release.wait(timeout=6), "Synthetic barrier timeout"
    monkeypatch.setattr(patients, "lock_selected_cephalo_for_archive", delayed, raising=False)
    # The route uses a function-local import; patch the exported function
    # at its source instead.
    monkeypatch.setattr(cephalo_document_lock, "lock_selected_cephalo_for_archive", delayed)

    def first():
        threading.current_thread().name = "first_s2b_archive"
        response = _run_route(engine, a)
        completed.append("first")
        return response

    def second():
        assert entered.wait(timeout=6)
        second_started.set()
        response = _run_route(engine, b)
        completed.append("second")
        return response

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(first)
        f2 = pool.submit(second)
        assert entered.wait(timeout=6)
        assert second_started.wait(timeout=6)
        assert not f2.done(), "Concurrent approver bypassed SQLite study lock"
        assert not completed
        release.set()
        first_result = f1.result(timeout=15)
        second_result = f2.result(timeout=15)

    assert first_result[0] == 200
    assert first_result[2] == original
    assert first_result[1]["x-cephalo-archive-replayed"] == "false"
    if different_pdf:
        assert second_result[0] == 409, second_result
    else:
        assert second_result[0] == 200, second_result
        assert second_result[1]["x-cephalo-archive-replayed"] == "true"
        assert second_result[2] == original

    with Session(engine) as db:
        rows = db.query(models.DocumentArchive).all()
        assert len(rows) == 1, "Exactly one official archive may exist for a revision"
        assert verified_official_archive_bytes(rows[0], db) == original
        audits = db.query(models.AuditLog).filter(
            models.AuditLog.action == "CEPH_A4_DESCRIPTIVE_APPROVED",
        ).all()
        assert len(audits) == 1, "Replay must not record a second approval"
    assert not list((root / ".cephalo-pending").rglob("*.json"))
    assert len(list(root.rglob("*.pdf"))) == 1


def test_s2b_exact_byte_recovery_reuses_precrash_pdf_and_rejects_other_pdf(
    s2b_sqlite,
):
    engine, root = s2b_sqlite
    original = _pdf(1)
    replacement = _pdf(2)
    digest = approval.archive_payload_digest(
        user_id=44, pdf_sha256=hashlib.sha256(original).hexdigest(),
        source_sha256=_source(engine),
    )
    proposed = root / "8001" / models.DocumentType.RAPPORT_CEPHALO.value / "2026" / "11" / "candidate.pdf"
    proposed.parent.mkdir(parents=True, exist_ok=True)
    with Session(engine) as db:
        # Simulate hard crash after journal+PDF flush and before SQL commit:
        # original immutable pending PDF survives, SQL archive is absent.
        first = prepare_official_pdf(
            db, root=root, proposed_path=proposed,
            patient_id=8001, analysis_id=9001, revision=3,
            payload_digest=digest, content=original,
        )
        assert first.content == original and first.newly_written
        db.rollback()
    assert proposed.read_bytes() == original
    assert list((root / ".cephalo-pending").rglob("*.json"))
    with Session(engine) as db:
        with pytest.raises(RuntimeError, match="conflit"):
            prepare_official_pdf(
                db, root=root, proposed_path=proposed.with_name("forged.pdf"),
                patient_id=8001, analysis_id=9001, revision=3,
                payload_digest=approval.archive_payload_digest(
                    user_id=44, pdf_sha256=hashlib.sha256(replacement).hexdigest(),
                    source_sha256=_source(engine),
                ),
                content=replacement,
            )
        db.rollback()
    assert proposed.read_bytes() == original
    # The same approved PDF is permitted to finish the existing journal,
    # with no newly written unreferenced PDF.
    outcome = _run_route(engine, _payload(engine, pdf=original))
    assert outcome[0] == 200, outcome
    assert outcome[2] == original
    with Session(engine) as db:
        rows = db.query(models.DocumentArchive).all()
        assert len(rows) == 1
        assert verified_official_archive_bytes(rows[0], db) == original
    assert not list((root / ".cephalo-pending").rglob("*.json"))
    assert len(list(root.rglob("*.pdf"))) == 1
