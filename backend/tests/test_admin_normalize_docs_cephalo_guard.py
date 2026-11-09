"""Authentic admin API regression: ambiguous historical document types are NOT signed reports.

Synthetic tenant/archive records only; no patient data or production migration.
"""
import pytest
from sqlalchemy import text

from backend import models
from backend.tests.test_cephalo_p2ter_atomic_archive import _case
from backend.tests.p2ter_bridge_synthetic_support import (
    _cabinet, _seed_synthetic_historical_cephalo_archive,
)


@pytest.mark.parametrize("legacy_label", ("bilan", "BILAN", "rapport_cephalo"))
def test_admin_normalize_docs_does_not_promote_unsigned_legacy_bilans(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path, legacy_label,
):
    from backend.services import archive_service

    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    historical, _ = _seed_synthetic_historical_cephalo_archive(db, patient, study)
    historical_id = historical.id
    legacy_path = historical.file_path
    original_hash = historical.file_hash
    # Emulate ONLY the database type spelling present in an old cabinet.
    # Do not fabricate a practitioner signature or alter the archived bytes.
    db.execute(
        text("UPDATE document_archives SET document_type = :legacy WHERE id = :id"),
        {"legacy": legacy_label, "id": historical_id},
    )
    db.commit()

    before = db.execute(text(
        "SELECT document_type,file_hash,file_path FROM document_archives WHERE id = :id"
    ), {"id": historical_id}).one()
    assert before.document_type == legacy_label

    result = client.post("/api/admin/normalize-docs", headers=auth_headers)
    assert result.status_code == 200, result.text[:300]
    assert result.json()["cephalo_legacy_reclassification"] == "HELD_UNVERIFIED_SIGNATURE"

    after = db.execute(text(
        "SELECT document_type,file_hash,file_path FROM document_archives WHERE id = :id"
    ), {"id": historical_id}).one()
    assert after.document_type == legacy_label, "Unsafe implicit promotion to official report"
    assert after.file_hash == original_hash
    assert after.file_path == legacy_path
    assert db.query(models.Patient).filter(models.Patient.id == patient.id).count() == 1
