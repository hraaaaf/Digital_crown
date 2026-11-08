"""CPV2-02C operator STOP checklist: synthetic-only, no clinical writes."""
from __future__ import annotations

import copy
import hashlib
import io
import sqlite3
import zipfile

import pytest

from backend.services.pocket_document_inventory import inventory_pocket_archive_readonly
from backend.services.pocket_document_review_policy import triage_pocket_document_inventory

PDF = b"%PDF-1.4\nsynthetic data only\n%%EOF\n"
PATH = "archives/100/CERTIFICAT/2026/11/synthetic.pdf"
ORPHAN = "documents/2026/11/orphan.pdf"


def _fixture(*, media=None, receipt=None, path="static/" + PATH, pdf=PDF):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE document_archives(id INTEGER, patient_id INTEGER, document_type TEXT, file_path TEXT, file_hash TEXT, file_size INTEGER, status TEXT)")
    db.execute("INSERT INTO document_archives VALUES(1, 100, 'CERTIFICAT', ?, ?, ?, 'ACTIF')", (path, hashlib.sha256(PDF).hexdigest(), len(PDF)))
    if receipt:
        db.execute("CREATE TABLE mobile_document_archive_receipts(id INTEGER, state TEXT)")
        db.execute("INSERT INTO mobile_document_archive_receipts VALUES(1,?)", (receipt,))
    db.commit()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as output:
        for key, content in (media if media is not None else [(PATH, pdf)]):
            output.writestr(key, content)
    before = hashlib.sha256(buffer.getvalue()).hexdigest()
    buffer.seek(0)
    return db, zipfile.ZipFile(buffer), before


def _report(db, media):
    return triage_pocket_document_inventory(inventory_pocket_archive_readonly(db, media))


def _assert_never_permitted(report):
    assert report["operator_gate"] == "HUMAN_REVIEW_REQUIRED"
    assert all(report[field] is False for field in (
        "allow_archive_replay", "allow_sql_mutation", "allow_media_delete",
        "allow_reassociation", "allow_restore", "allow_clinical_release",
    ))


def test_all_matched_legacy_is_evidence_only_not_approved():
    db, media, _ = _fixture(path="static/documents/2026/11/synthetic.pdf", media=[("documents/2026/11/synthetic.pdf", PDF)])
    try:
        report = _report(db, media)
        assert report["decision"] == "BYTE_MATCH_EVIDENCE_ONLY"
        assert report["matched_count"] == 1
        _assert_never_permitted(report)
    finally:
        db.close(); media.close()


@pytest.mark.parametrize("state", ["PROCESSING", "REVIEW_REQUIRED"])
def test_unresolved_receipt_never_replays(state):
    db, media, _ = _fixture(receipt=state)
    try:
        report = _report(db, media)
        assert report["decision"] == "HOLD_MANUAL_REVIEW"
        assert "INCOMPLETE_RECEIPT" in report["reason_codes"]
        _assert_never_permitted(report)
    finally:
        db.close(); media.close()


def test_orphan_media_never_proves_ownership():
    db, media, _ = _fixture(media=[(PATH, PDF), (ORPHAN, PDF + b"orphan")])
    try:
        report = _report(db, media)
        assert report["decision"] == "HOLD_MANUAL_REVIEW"
        assert "UNLINKED_MEDIA" in report["reason_codes"]
        _assert_never_permitted(report)
        assert ORPHAN not in repr(report)
    finally:
        db.close(); media.close()


def test_processing_with_orphan_stays_unresolved_and_unchanged():
    db, media, zip_before = _fixture(receipt="PROCESSING", media=[(PATH, PDF), (ORPHAN, PDF)])
    try:
        sql_before = tuple(db.iterdump())
        report = _report(db, media)
        assert report["decision"] == "HOLD_MANUAL_REVIEW"
        assert {"INCOMPLETE_RECEIPT", "UNLINKED_MEDIA"}.issubset(report["reason_codes"])
        assert tuple(db.iterdump()) == sql_before
        assert hashlib.sha256(media.fp.getvalue()).hexdigest() == zip_before
        _assert_never_permitted(report)
    finally:
        db.close(); media.close()


def test_changed_pdf_same_size_is_not_reassociated():
    changed = PDF.replace(b"synthetic", b"alteredXX")
    assert len(changed) == len(PDF)
    db, media, _ = _fixture(pdf=changed)
    try:
        report = _report(db, media)
        assert "SHA256_MISMATCH" in report["reason_codes"]
        assert report["decision"] == "HOLD_MANUAL_REVIEW"
        _assert_never_permitted(report)
    finally:
        db.close(); media.close()


def test_missing_pdf_stops_operator():
    db, media, _ = _fixture(media=[])
    try:
        report = _report(db, media)
        assert "MISSING_MEDIA" in report["reason_codes"]
        _assert_never_permitted(report)
    finally:
        db.close(); media.close()


def test_unknown_historical_path_stops_operator():
    db, media, _ = _fixture(path="static/unmapped/2026/11/synthetic.pdf", media=[("unmapped/2026/11/synthetic.pdf", PDF)])
    try:
        report = _report(db, media)
        assert "UNSUPPORTED_SQL_PATH" in report["reason_codes"]
        _assert_never_permitted(report)
    finally:
        db.close(); media.close()


def test_empty_inventory_cannot_return_green():
    report = triage_pocket_document_inventory({"status": "BYTE_INVENTORY_MATCHED_NOT_RESTORE_APPROVED", "entries": []})
    assert report["decision"] == "HOLD_MANUAL_REVIEW"
    _assert_never_permitted(report)


def test_malformed_manifest_fails_closed_without_injection_leaks():
    secret = "patient-secret-do-not-echo"
    report = triage_pocket_document_inventory({"status": "REVIEW_REQUIRED", "entries": [
        {"source": "ZIP", "status": "REVIEW_REQUIRED", "reason": secret, "path": secret}
    ]})
    assert report["decision"] == "HOLD_MANUAL_REVIEW"
    assert report["reason_codes"] == ["UNKNOWN_ANOMALY"]
    assert secret not in repr(report)
    _assert_never_permitted(report)


def test_contradictory_manifest_does_not_get_approved():
    report = triage_pocket_document_inventory({"status": "BYTE_INVENTORY_MATCHED_NOT_RESTORE_APPROVED", "entries": [
        {"source": "SQL", "status": "REVIEW_REQUIRED", "reason": "MISSING_MEDIA"},
    ]})
    assert report["decision"] == "HOLD_MANUAL_REVIEW"
    assert report["reason_codes"] == ["INCONSISTENT_MANIFEST"]
    _assert_never_permitted(report)


def test_unknown_entry_source_is_fail_closed():
    report = triage_pocket_document_inventory({"status": "REVIEW_REQUIRED", "entries": [
        {"source": "RECOVERY", "status": "MATCHED", "reason": None},
    ]})
    assert report["decision"] == "HOLD_MANUAL_REVIEW"
    assert report["reason_codes"] == ["INVALID_ENTRY"]
    _assert_never_permitted(report)


def test_input_remains_unmodified():
    manifest = {"status": "REVIEW_REQUIRED", "entries": [
        {"source": "RECEIPT", "status": "REVIEW_REQUIRED", "reason": "INCOMPLETE_RECEIPT", "receipt_row": 5},
    ]}
    original = copy.deepcopy(manifest)
    report = triage_pocket_document_inventory(manifest)
    assert manifest == original
    assert "receipt_row" not in report
    _assert_never_permitted(report)


@pytest.mark.parametrize("manifest", [
    {"status": [], "entries": []},
    {"status": "REVIEW_REQUIRED", "entries": [{"source": [], "status": "MATCHED"}]},
    {"status": "REVIEW_REQUIRED", "entries": [{"source": "ZIP", "status": "REVIEW_REQUIRED", "reason": []}]},
])
def test_unhashable_untrusted_values_fail_closed(manifest):
    report = triage_pocket_document_inventory(manifest)
    assert report["decision"] == "HOLD_MANUAL_REVIEW"
    _assert_never_permitted(report)
