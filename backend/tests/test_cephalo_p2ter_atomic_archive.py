"""P2ter++: real concurrent SQLite connections + authenticated archive idempotency.

No patient data or clinical approval: fixtures are synthetic T2 only.
"""
from __future__ import annotations

import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from sqlalchemy import create_engine, update
from sqlalchemy.orm import Session

from backend import models
from backend.services.cephalo_document_lock import lock_selected_cephalo_for_archive
from backend.tests.test_cephalo_r23g5_authenticated_api import _case, _jwt, PATH
from backend.tests.test_cephalo_p2bis_http_pdf_continuity import _cabinet, _temporary_pdf_output


def test_database_row_guard_blocks_actual_concurrent_revision_write(tmp_path):
    """Two separate DB connections: editing must wait until PDF transaction ends."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'real-concurrency.db'}",
        connect_args={"check_same_thread": False, "timeout": 4},
    )
    models.CephaloAnalysis.__table__.create(engine)
    with engine.begin() as conn:
        conn.execute(models.CephaloAnalysis.__table__.insert().values(
            id=37, patient_id=44, image_original_path="t2-synthetic.png",
            landmarks_data=[], angles_data={"test_revision": 1},
        ))

    locked, allow_commit, began_edit, edit_done = (
        threading.Event(), threading.Event(), threading.Event(), threading.Event()
    )
    order = []

    def archive_transaction():
        with Session(engine) as db:
            lock_selected_cephalo_for_archive(db, patient_id=44, analysis_id=37)
            order.append("archive_acquired")
            locked.set()
            assert allow_commit.wait(timeout=3)
            db.commit()
            order.append("archive_committed")

    def clinical_revision_update():
        assert locked.wait(timeout=3)
        with Session(engine) as db:
            began_edit.set()
            db.execute(
                update(models.CephaloAnalysis)
                .where(models.CephaloAnalysis.id == 37)
                .values(angles_data={"test_revision": 2})
            )
            db.commit()
            order.append("edit_committed")
            edit_done.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(archive_transaction)
        b = pool.submit(clinical_revision_update)
        try:
            assert began_edit.wait(timeout=3)
            assert not edit_done.wait(timeout=0.15), (
                "Concurrent revision edit committed while the archive study lock was held"
            )
        finally:
            allow_commit.set()
        a.result(timeout=5)
        b.result(timeout=5)
    assert order == ["archive_acquired", "archive_committed", "edit_committed"]
    with Session(engine) as db:
        assert db.get(models.CephaloAnalysis, 37).angles_data == {"test_revision": 2}
    engine.dispose()


def test_same_study_revision_archive_replays_identical_bytes_once(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, points = _case(db, dentiste)
    headers = {**_jwt(client, dentiste), "Origin": "http://127.0.0.1:5173"}
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services import archive_service

    # Synthetic-only bypass for transport/archive concurrency. No clinical approval.
    from types import SimpleNamespace
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _: SimpleNamespace(is_valid=True, warnings=[], fatals=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")

    endpoint = f"/api/patients/{patient.id}/pdf"
    payload = {"analysis_id": study.id, "expected_revision": 1, "archive": True}
    first = client.post(endpoint, json=payload, headers=headers)
    assert first.status_code == 200, first.text[:250] if first.status_code != 200 else ""
    assert first.headers.get("X-Cephalo-Archive-Replayed") is None
    second = client.post(endpoint, json=payload, headers=headers)
    assert second.status_code == 200, second.text[:250] if second.status_code != 200 else ""
    assert second.headers["X-Cephalo-Archive-Replayed"] == "true"
    # Browser Fetch cannot read non-safelisted headers without this CORS contract.
    assert second.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    exposed = {h.strip().lower() for h in second.headers["access-control-expose-headers"].split(",")}
    assert "x-cephalo-archive-replayed" in exposed
    assert {"x-cephalo-analysis-id", "x-cephalo-revision"} <= exposed
    assert second.content == first.content
    changed_context = client.post(
        endpoint, json={**payload, "ai_diagnostic": {"diagnostic": "CHANGED SYNTHETIC"}},
        headers=headers,
    )
    assert changed_context.status_code == 409, changed_context.text[:250]
    assert "contexte clinique" in changed_context.json()["detail"]

    records = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).all()
    assert len(records) == 1
    assert records[0].clinical_data["cephalo_analysis_revision"] == 1

    # Integrity failures must refuse rather than silently mint a replacement.
    archived_file = tmp_path / "archives" / records[0].file_path.removeprefix("static/archives/")
    saved = archived_file.read_bytes()
    archived_file.write_bytes(saved + b"tampered")
    refused = client.post(endpoint, json=payload, headers=headers)
    assert refused.status_code == 409
    assert len(db.query(models.DocumentArchive).filter(
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).all()) == 1


def test_generic_upload_cannot_forge_or_overwrite_official_cephalo_archive(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """Blind-first adversarial route test: auth + PDF bytes do not confer authority."""
    from types import SimpleNamespace
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services import archive_service

    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    query = {"patient_id": patient.id, "doc_type": "RAPPORT_CEPHALO"}

    # First, upload with a plausible PDF mime; no bound study/revision provided.
    forged = client.post(
        "/api/documents/archive",
        params=query,
        files={"file": ("counterfeit.pdf", b"%PDF-1.4 T2 fake", "application/pdf")},
        headers=headers,
    )
    assert forged.status_code == 422, forged.text
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0

    # Create an actual synthetic authority-bound report, then attempt generic
    # overwrite of its original filename. Neither its bytes nor SQL may mutate.
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _: SimpleNamespace(is_valid=True, warnings=[], fatals=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    official = client.post(
        f"/api/patients/{patient.id}/pdf",
        json={"analysis_id": study.id, "expected_revision": 1, "archive": True},
        headers=headers,
    )
    assert official.status_code == 200, official.text[:300] if official.status_code != 200 else ""
    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).one()
    before_hash, before_file, before_id = doc.file_hash, doc.file_path, doc.analysis_id
    fake_overwrite = client.post(
        "/api/documents/archive",
        params={**query, "on_conflict": "OVERWRITE"},
        files={"file": (doc.original_filename, b"%PDF-1.4 altered", "application/pdf")},
        headers=headers,
    )
    assert fake_overwrite.status_code == 422, fake_overwrite.text
    db.refresh(doc)
    assert (doc.file_hash, doc.file_path, doc.analysis_id) == (
        before_hash, before_file, before_id,
    )
    persisted = (tmp_path / "archives" / before_file.removeprefix("static/archives/")).read_bytes()
    assert persisted == official.content
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 1


def test_official_archive_sql_commit_failure_removes_orphaned_pdf(
    db, monkeypatch, tmp_path,
):
    import pytest
    from backend.services import archive_service

    archive_root = tmp_path / "private-archive"
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", archive_root)
    writer = archive_service.ArchiveService(db)
    monkeypatch.setattr(writer, "check_conflicts", lambda *args, **kwargs: {"has_conflict": False})

    def reject_commit():
        raise OSError("synthetic database commit interruption")

    with monkeypatch.context() as patch:
        patch.setattr(db, "commit", reject_commit)
        with pytest.raises(OSError, match="synthetic database"):
            writer.archive_document(
                patient_id=97531, analysis_id=86420,
                file_content=b"%PDF-T2-ONLY-SYNTHETIC",
                filename="t2-commit-interruption.pdf",
                doc_type=models.DocumentType.RAPPORT_CEPHALO,
                uploaded_by_id=None,
                clinical_data={
                    "cephalo_analysis_id": 86420,
                    "cephalo_analysis_revision": 1,
                    "cephalo_archive_payload_digest": "synthetic",
                },
            )
    assert not list(archive_root.rglob("*.pdf")), (
        "Failed SQL commit left a potentially exposed official report file"
    )


def test_archive_revision_edit_after_first_commit_is_not_replayed_as_old_revision(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    from types import SimpleNamespace
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services import archive_service
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _: SimpleNamespace(is_valid=True, warnings=[], fatals=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "archives")
    path = f"/api/patients/{patient.id}/pdf"
    req1 = {"analysis_id": study.id, "expected_revision": 1, "archive": True}
    assert client.post(path, json=req1, headers=headers).status_code == 200
    edited = deepcopy(points)
    next(p for p in edited if p["id"] == "A")["x"] += 2
    assert client.put(PATH + str(study.id), json={"landmarks": edited}, headers=headers).status_code == 200
    assert client.post(path, json=req1, headers=headers).status_code == 409
    updated = client.post(
        path,
        json={"analysis_id": study.id, "expected_revision": 2, "archive": True},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text[:250] if updated.status_code != 200 else ""
    archives = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.analysis_id == study.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).all()
    assert len(archives) == 2
    assert sorted(a.clinical_data["cephalo_analysis_revision"] for a in archives) == [1, 2]
