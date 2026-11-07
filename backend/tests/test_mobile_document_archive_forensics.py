"""Privacy-minimal, strictly read-only Pocket incident assessments.

All data is synthetic, uses conftest's in-memory SQLite and tmp_path media.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException

from backend import models
from backend.services.mobile_document_archive_forensics import (
    inspect_archive_receipt_read_only,
)
from backend.services.mobile_document_archive_receipts import (
    claim_archive_intent, complete_archive_in_current_transaction,
    mark_unresolved_for_manual_review, read_scoped_receipt,
)


def _identity(owner_id, patient_id, key):
    return dict(
        tenant_id=owner_id, actor_id=owner_id, device_id="paired-test-01",
        key=key, patient_id=patient_id, document_type="certificat",
        request_sha256="a" * 64,
    )


def _inspect(db, tmp_path, identity):
    return inspect_archive_receipt_read_only(
        db, tenant_id=identity["tenant_id"], actor_id=identity["actor_id"],
        device_id=identity["device_id"], key=identity["key"],
        media_root=tmp_path,
    )


def test_process_crash_receipt_stays_locked_with_zero_mutation(db, dentiste, tmp_path):
    identity = _identity(dentiste.id, 9991, str(uuid.uuid4()))
    receipt, claimed = claim_archive_intent(db, **identity)
    assert claimed
    report = _inspect(db, tmp_path, identity)
    assert report == {
        "receipt_state": "PROCESSING", "verified_archive": False,
        "automatic_replay_allowed": False, "decision": "HOLD_FOR_MANUAL_REVIEW",
    }
    db.expire_all()
    stored = read_scoped_receipt(
        db, tenant_id=dentiste.id, actor_id=dentiste.id,
        device_id="paired-test-01", key=identity["key"],
    )
    assert stored.id == receipt.id
    assert stored.state == "PROCESSING" and stored.archive_id is None


def test_review_required_is_not_reinterpreted_as_success(db, dentiste, tmp_path):
    identity = _identity(dentiste.id, 9992, str(uuid.uuid4()))
    receipt, _ = claim_archive_intent(db, **identity)
    mark_unresolved_for_manual_review(db, receipt.id)
    report = _inspect(db, tmp_path, identity)
    assert report["decision"] == "HOLD_FOR_MANUAL_REVIEW"
    assert report["verified_archive"] is False
    assert report["automatic_replay_allowed"] is False
    assert read_scoped_receipt(
        db, tenant_id=dentiste.id, actor_id=dentiste.id,
        device_id="paired-test-01", key=identity["key"],
    ).state == "REVIEW_REQUIRED"


def test_cross_device_cannot_inspect_receipt(db, dentiste, tmp_path):
    identity = _identity(dentiste.id, 9993, str(uuid.uuid4()))
    claim_archive_intent(db, **identity)
    with pytest.raises(HTTPException) as exc:
        inspect_archive_receipt_read_only(
            db, tenant_id=dentiste.id, actor_id=dentiste.id,
            device_id="different-device", key=identity["key"], media_root=tmp_path,
        )
    assert exc.value.status_code == 404


def test_completed_pdf_verifies_only_when_sql_patient_scope_and_bytes_match(
    db, dentiste, tmp_path,
):
    patient = models.Patient(
        nom="FICTIF", prenom="RECU", sexe="F",
        date_naissance=datetime(1994, 1, 1), employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    media = tmp_path / "archives"
    media.mkdir()
    content = b"%PDF-1.4\nsynthetic-only-not-a-real-patient\n%%EOF\n"
    (media / "proof.pdf").write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    doc = models.DocumentArchive(
        patient_id=patient.id, uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.CERTIFICAT,
        filename="proof.pdf", original_filename="proof.pdf",
        document_group_id=str(uuid.uuid4()), version_number=1,
        is_latest_version=True, file_hash=digest, file_size=len(content),
        file_path="static/archives/proof.pdf", status=models.DocumentStatus.ACTIF,
        clinical_data={}, tags=[],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    identity = _identity(dentiste.id, patient.id, str(uuid.uuid4()))
    receipt, claimed = claim_archive_intent(db, **identity)
    assert claimed
    db.info["_mobile_document_archive_receipt_id"] = receipt.id
    complete_archive_in_current_transaction(db, archive=doc)
    db.info.pop("_mobile_document_archive_receipt_id")
    db.commit()

    proof = _inspect(db, tmp_path, identity)
    assert proof["receipt_state"] == "COMPLETED"
    assert proof["verified_archive"] is True
    assert proof["decision"] == "EXISTING_ARCHIVE_VERIFIED"
    assert proof["automatic_replay_allowed"] is False
    assert "patient_id" not in proof and "file_path" not in proof

    (media / "proof.pdf").write_bytes(content + b"tampering")
    corrupted = _inspect(db, tmp_path, identity)
    assert corrupted["verified_archive"] is False
    assert corrupted["decision"] == "PDF_HASH_MISMATCH"
    assert corrupted["automatic_replay_allowed"] is False

    doc.file_path = "static/archives/../../outside.pdf"
    db.commit()
    invalid_path = _inspect(db, tmp_path, identity)
    assert invalid_path["decision"] == "UNSAFE_ARCHIVE_PATH"
    assert invalid_path["verified_archive"] is False
