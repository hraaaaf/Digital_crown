"""CPV2-02C crash-window FUE: real ArchiveService and two fictional PDF paths.

This test-only file exercises abrupt worker termination at the legacy mirror
copy boundary. No production schema, cabinet data, migration or auto-repair.
The *unresolved* archive receipt must remain non-replayable after restart.
"""
from __future__ import annotations

import hashlib
import io
import multiprocessing
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from reportlab.pdfgen import canvas

from backend import models
from backend.core.runtime_safety import database_target_fingerprint
from backend.services.mobile_document_archive_forensics import inspect_archive_receipt_read_only
from backend.services.mobile_document_archive_receipts import (
    MobileDocumentArchiveReceipt,
    PocketReceiptBase,
    claim_archive_intent,
    read_scoped_receipt,
)

# Entirely fictional PDF, never a real patient document. One stable digest
# makes it possible to prove *both* physical copies without logging a path.
def _fictional_pdf_bytes() -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(420, 595), invariant=1)
    pdf.drawString(48, 520, "FICTITIOUS TEST CERTIFICATE - NO PATIENT")
    pdf.drawString(48, 500, "Disposable crash-window laboratory only")
    pdf.save()
    data = output.getvalue()
    assert data.startswith(b"%PDF-") and len(data) > 400
    return data
ACTOR = 97101
PATIENT = 97102
DEVICE = "test-only-paired-device"


def _crash_worker(db_file: str, media_dir: str, receipt_id: str, stage: str, fictional_pdf: bytes) -> None:
    """Child process hard-exits at copy2 without traceback, finally or rollback."""
    from backend.services import archive_service

    media = Path(media_dir)
    archive_service.MEDIA_DIR = media
    archive_service.ARCHIVE_BASE_DIR = media / "archives"
    archive_service.LEGACY_DOCS_DIR = media / "documents"
    real_copy = archive_service.shutil.copy2

    def crash_at_mirror(source, destination, *args, **kwargs):
        if stage == "before_mirror":
            os._exit(97)
        real_copy(source, destination, *args, **kwargs)
        os._exit(98)

    archive_service.shutil.copy2 = crash_at_mirror
    engine = create_engine("sqlite:///" + db_file)
    with Session(engine) as db:
        db.info["_mobile_document_archive_receipt_id"] = receipt_id
        archive_service.ArchiveService(db).archive_document(
            patient_id=PATIENT,
            uploaded_by_id=ACTOR,
            filename="fictional-certificate.pdf",
            file_content=fictional_pdf,
            doc_type=models.DocumentType.CERTIFICAT,
            title="Fictional only",
            clinical_data={},
        )
    # Reaching this point is a regression; the requested crash was bypassed.
    os._exit(99)


@pytest.mark.parametrize(
    ("stage", "exit_code", "expected_legacy"),
    [("before_mirror", 97, False), ("after_mirror", 98, True)],
)
def test_real_abrupt_death_never_replays_or_loses_orphan_evidence(
    tmp_path, monkeypatch, stage, exit_code, expected_legacy,
):
    """Fresh-process durable receipt + real primary/mirror files, no cleanup."""
    db_file = tmp_path / "fixture-only-persistent.db"
    media = tmp_path / "fixture-only-media"
    media.mkdir()
    engine = create_engine("sqlite:///" + str(db_file))
    # Small, real canonical schema subset (not synthetic_archive_links).
    models.Base.metadata.create_all(
        engine,
        tables=[models.User.__table__, models.Patient.__table__, models.DocumentArchive.__table__],
    )
    PocketReceiptBase.metadata.create_all(engine)
    key = str(uuid4())
    identity = dict(
        tenant_id=ACTOR, actor_id=ACTOR, device_id=DEVICE, key=key,
        patient_id=PATIENT, document_type="certificat", request_sha256="b" * 64,
    )
    with engine.begin() as conn:
        conn.execute(models.User.__table__.insert().values(
            id=ACTOR, email="fictional-only@example.invalid", hashed_password="not-a-login",
            role=models.UserRole.DENTISTE, nom_complet="Fictional Dentist",
        ))
        conn.execute(models.Patient.__table__.insert().values(
            id=PATIENT, employer_id=ACTOR, nom="FICTIF", prenom="TEST",
            sexe="F", date_naissance=datetime(1995, 1, 1),
        ))
    with Session(engine) as db:
        receipt, claimed = claim_archive_intent(db, **identity)
        assert claimed and receipt.state == "PROCESSING"
        receipt_id = receipt.id

    engine.dispose()
    fictional_pdf = _fictional_pdf_bytes()
    fictional_digest = hashlib.sha256(fictional_pdf).hexdigest()
    child = multiprocessing.get_context("spawn").Process(
        target=_crash_worker,
        args=(str(db_file), str(media), receipt_id, stage, fictional_pdf),
    )
    child.start()
    child.join(timeout=60)
    if child.is_alive():
        child.terminate()
        child.join(timeout=10)
        pytest.fail("Crash FUE worker did not reach the deterministic termination point")
    assert child.exitcode == exit_code, "ArchiveService failed before the requested crash checkpoint"

    # Inspect unchanged, physically stored evidence after the worker is gone.
    primary_files = list((media / "archives").rglob("*.pdf"))
    legacy_files = list((media / "documents").rglob("*.pdf"))
    assert len(primary_files) == 1
    assert len(legacy_files) == int(expected_legacy)
    assert hashlib.sha256(primary_files[0].read_bytes()).hexdigest() == fictional_digest
    if expected_legacy:
        assert hashlib.sha256(legacy_files[0].read_bytes()).hexdigest() == fictional_digest

    url = "sqlite:///" + str(db_file)
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    monkeypatch.setenv("DIGITALCROWN_ISOLATION_DB_FINGERPRINT", database_target_fingerprint(url))
    reopened = create_engine(url)
    try:
        with Session(reopened) as db:
            assert db.query(models.DocumentArchive).count() == 0
            assert db.scalar(select(func.count()).select_from(MobileDocumentArchiveReceipt)) == 1
            current = read_scoped_receipt(
                db, tenant_id=ACTOR, actor_id=ACTOR, device_id=DEVICE, key=key,
            )
            assert current.state == "PROCESSING"
            assert current.archive_id is None and current.archive_sha256 is None
            report = inspect_archive_receipt_read_only(
                db, tenant_id=ACTOR, actor_id=ACTOR,
                device_id=DEVICE, key=key, media_root=media,
            )
            assert report == {
                "receipt_state": "PROCESSING", "verified_archive": False,
                "automatic_replay_allowed": False, "decision": "HOLD_FOR_MANUAL_REVIEW",
            }
            # An HTTP retry with the *same* intent must NOT generate a new PDF.
            existing, new_claim = claim_archive_intent(db, **identity)
            assert not new_claim and existing.id == receipt_id
            assert existing.state == "PROCESSING"
            assert db.query(models.DocumentArchive).count() == 0
    finally:
        reopened.dispose()

    # Read-only forensics must neither unlink nor misclassify these clinical
    # remnants. A later owner-reviewed quarantine/recovery gate owns cleanup.
    assert len(list((media / "archives").rglob("*.pdf"))) == 1
    assert len(list((media / "documents").rglob("*.pdf"))) == int(expected_legacy)
