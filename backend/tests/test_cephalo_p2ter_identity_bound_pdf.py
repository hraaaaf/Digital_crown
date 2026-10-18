"""P2ter: actual JWT FastAPI and PDF bytes bound to the selected synthetic study.

All patients are fabricated; all SQL is StaticPool in-memory and PDFs stay in
pytest tmp_path. Clinical authorization/norms are never asserted by this test.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import fitz
from backend import models
from backend.tests.test_cephalo_r23g5_authenticated_api import _case, _jwt, _read, PATH
from backend.tests.test_cephalo_p2bis_http_pdf_continuity import (
    _cabinet, _temporary_pdf_output,
)
from backend.tests.conftest import make_user
from backend.routers.documents import doc_factory
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def _request(client, patient_id, study_id, headers, revision=1, archive=False):
    return client.post(
        f"/api/patients/{patient_id}/pdf",
        json={"analysis_id": study_id, "expected_revision": revision, "archive": archive},
        headers=headers,
    )


def _text(pdf):
    assert pdf.content[:4] == b"%PDF"
    with fitz.open(stream=pdf.content, filetype="pdf") as doc:
        assert len(doc) >= 2
        assert all(p.rect.width > 0 and p.rect.height > 0 for p in doc)
        return "\n".join(page.get_text() for page in doc)


def _compact(t):
    return "".join(c for c in t if c.isalnum()).casefold()


def _second(db, first):
    # Two different records of the SAME test patient, with distinct source IDs.
    newer = models.CephaloAnalysis(
        patient_id=first.patient_id,
        image_original_path=first.image_original_path,
        landmarks_data=deepcopy(first.landmarks_data),
        angles_data=deepcopy(first.angles_data),
        is_calibrated=False,
        mm_per_pixel=None,
    )
    db.add(newer)
    db.commit()
    db.refresh(newer)
    assert newer.id > first.id
    return newer


def test_two_studies_older_selection_generates_exact_study_and_revision(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study_a, _ = _case(db, dentiste)
    study_b = _second(db, study_a)
    headers = _jwt(client, dentiste)

    first_read, a = _read(client, study_a.id, headers)
    second_read, b = _read(client, study_b.id, headers)
    assert a["revision"] == b["revision"] == 1
    assert first_read["id"] != second_read["id"]

    checked = client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": study_a.id, "expected_revision": 1},
        headers=headers,
    )
    assert checked.status_code == 200, checked.text[:500]
    assert checked.json()["analysis_id"] == study_a.id
    assert checked.json()["analysis_revision"] == 1

    pdf_a = _request(client, patient.id, study_a.id, headers)
    assert pdf_a.status_code == 200, pdf_a.text[:500] if pdf_a.status_code != 200 else ""
    assert pdf_a.headers["X-Cephalo-Analysis-Id"] == str(study_a.id)
    assert pdf_a.headers["X-Cephalo-Revision"] == "1"
    # Export A4 images from the exact PDF bytes for human QA; synthetic only.
    import os
    evidence_dir = os.getenv("P2TER_EVIDENCE_DIR")
    if evidence_dir:
        out = Path(evidence_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "selected-old-study-a.pdf").write_bytes(pdf_a.content)
        with fitz.open(stream=pdf_a.content, filetype="pdf") as pages:
            for index, page in enumerate(pages):
                assert 590 < page.rect.width < 600 and 838 < page.rect.height < 845
                if index < 12:
                    page.get_pixmap(matrix=fitz.Matrix(1.2, 1.2), alpha=False).save(
                        out / f"selected-old-study-a-page-{index+1:02}.png"
                    )
    text_a = _compact(_text(pdf_a))
    assert _compact(f"ÉTUDE CÉPHALO ID : {study_a.id}") in text_a
    assert _compact(f"ÉTUDE CÉPHALO ID : {study_b.id}") not in text_a

    pdf_b = _request(client, patient.id, study_b.id, headers)
    assert pdf_b.status_code == 200
    assert pdf_b.headers["X-Cephalo-Analysis-Id"] == str(study_b.id)
    text_b = _compact(_text(pdf_b))
    assert _compact(f"ÉTUDE CÉPHALO ID : {study_b.id}") in text_b
    assert len(list(tmp_path.glob("*.pdf"))) == 2


def test_missing_mismatched_and_cross_tenant_study_fails_without_files(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study_a, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)

    # Missing selection is a schema error; there is no latest-study fallback.
    no_id = client.post(f"/api/patients/{patient.id}/pdf", json={"archive": False}, headers=headers)
    assert no_id.status_code == 422
    for invalid in [0, -1, "last", True, None]:
        response = client.post(
            f"/api/patients/{patient.id}/pdf",
            json={"analysis_id": invalid, "expected_revision": 1, "archive": False},
            headers=headers,
        )
        assert response.status_code == 422
    invalid_study = _request(client, patient.id, 999999, headers)
    assert invalid_study.status_code == 404

    stranger, stranger_analysis, _ = _case(db, dentiste)
    assert stranger.id != patient.id
    assert _request(client, patient.id, stranger_analysis.id, headers).status_code == 404
    assert client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": stranger_analysis.id, "expected_revision": 1},
        headers=headers,
    ).status_code == 404

    # Existing analysis of a valid patient, but no bearer JWT or wrong tenant.
    client.cookies.clear()
    assert _request(client, patient.id, study_a.id, headers={}).status_code == 401
    outsider = make_user(db, email="p2ter-not-this-cabinet@cabinet.invalid")
    assert _request(client, patient.id, study_a.id, _jwt(client, outsider)).status_code == 403
    assert list(tmp_path.glob("*.pdf")) == []


def test_stale_revision_and_corrupted_evidence_reject_pdf_and_prevalidation(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study_a, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)

    no_revision = client.post(
        f"/api/patients/{patient.id}/pdf",
        json={"analysis_id": study_a.id, "archive": False}, headers=headers,
    )
    assert no_revision.status_code == 422
    edited = deepcopy(points)
    next(p for p in edited if p["id"] == "A")["x"] += 2
    assert client.put(PATH + str(study_a.id), json={"landmarks": edited}, headers=headers).status_code == 200
    assert _read(client, study_a.id, headers)[1]["revision"] == 2
    assert _request(client, patient.id, study_a.id, headers, revision=1).status_code == 409
    assert client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": study_a.id, "expected_revision": 1}, headers=headers,
    ).status_code == 409
    fresh = _request(client, patient.id, study_a.id, headers, revision=2)
    assert fresh.status_code == 200
    assert fresh.headers["X-Cephalo-Revision"] == "2"
    assert _compact("RÉVISION : 2") in _compact(_text(fresh))

    persisted = db.get(models.CephaloAnalysis, study_a.id)
    bad = deepcopy(persisted.angles_data)
    bad[EVIDENCE_GRAPH_KEY]["current_landmark_refs"] = []
    persisted.angles_data = bad
    db.commit()
    assert _request(client, patient.id, study_a.id, headers, revision=2).status_code == 409
    assert client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": study_a.id, "expected_revision": 2}, headers=headers,
    ).status_code == 409
    assert len(list(tmp_path.glob("*.pdf"))) == 1



def test_archiving_revision_changed_after_successful_prevalidation_fails_closed(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """Distinct HTTP calls: prevalidate revision 1, save revision 2, archive old revision.

    This tests a stale prevalidation boundary, NOT a simultaneous SQL row-lock race.
    """
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, old, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    pre = client.get(
        f"/api/patients/{patient.id}/cephalo-validation",
        params={"analysis_id": old.id, "expected_revision": 1},
        headers=headers,
    )
    assert pre.status_code == 200, pre.text
    assert pre.json()["analysis_id"] == old.id
    assert pre.json()["analysis_revision"] == 1
    edited = deepcopy(points)
    next(p for p in edited if p["id"] == "A")["x"] += 2
    update = client.put(PATH + str(old.id), json={"landmarks": edited}, headers=headers)
    assert update.status_code == 200, update.text
    assert _read(client, old.id, headers)[1]["revision"] == 2
    stale = _request(client, patient.id, old.id, headers, revision=1, archive=True)
    assert stale.status_code == 409
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0
    assert list(tmp_path.glob("*.pdf")) == []


def test_structural_consistency_failure_refuses_archive_without_writing_pdf(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """A synthetic structural refusal checks real FastAPI status and no write.

    An injected inconsistent validation result is *not* a scientific approval.
    """
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _data: SimpleNamespace(is_valid=False, fatals=["Discordance structurelle synthétique"], warnings=[]),
    )
    rejected = _request(client, patient.id, study.id, headers, archive=True)
    assert rejected.status_code == 422
    assert "Discordance structurelle synthétique" in rejected.json()["detail"]["fatals"]
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0
    assert list(tmp_path.glob("*.pdf")) == []
    assert db.query(models.CephaloArchiveClaim).filter(
        models.CephaloArchiveClaim.analysis_id == study.id,
    ).count() == 0


def test_archive_failure_is_not_silenced(client, db, dentiste, monkeypatch, tmp_path):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)

    # Synthetic validation bypass only to reach the I/O-failure branch; this
    # intentionally confers NO clinical authority on the fixture.
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _source: SimpleNamespace(is_valid=True, fatals=[], warnings=[]),
    )

    from backend.services.archive_service import ArchiveService
    def fail_archive(self, **kwargs):
        raise OSError("synthetic archive disk failure")
    monkeypatch.setattr(ArchiveService, "archive_document", fail_archive)
    from fastapi import HTTPException
    # The endpoint must never return 200 or silently claim the archive exists.
    try:
        response = _request(client, patient.id, study.id, headers, archive=True)
        assert response.status_code == 500
    except HTTPException as exc:
        assert exc.status_code == 500
    assert list(tmp_path.glob("*.pdf")) == []


def test_archive_persists_selected_study_fk_and_revision_on_synthetic_fixture(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, original, _ = _case(db, dentiste)
    newer = _second(db, original)
    headers = _jwt(client, dentiste)

    # Force only the consistency-validator branch to pass so that the archive
    # I/O contract can be tested. This is NEVER clinical approval.
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services import archive_service
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _data: SimpleNamespace(is_valid=True, warnings=[], fatals=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "isolated-archives")

    older_pdf = _request(client, patient.id, original.id, headers, archive=True)
    assert older_pdf.status_code == 200, older_pdf.text[:700] if older_pdf.status_code != 200 else ""
    assert older_pdf.headers["X-Cephalo-Analysis-Id"] == str(original.id)
    archived = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).all()
    assert len(archived) == 1
    assert archived[0].analysis_id == original.id
    assert archived[0].analysis_id != newer.id
    assert archived[0].clinical_data["cephalo_analysis_id"] == original.id
    assert archived[0].clinical_data["cephalo_analysis_revision"] == 1
    assert archived[0].file_path.startswith("static/archives/")
    relative = archived[0].file_path.removeprefix("static/archives/")
    saved = (tmp_path / "isolated-archives" / relative).read_bytes()
    assert saved == older_pdf.content
    assert _compact(f"ÉTUDE CÉPHALO ID : {original.id}") in _compact(_text(older_pdf))


def test_unversioned_historical_study_cannot_be_archived_as_authoritative(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    persisted = db.get(models.CephaloAnalysis, study.id)
    angles = deepcopy(persisted.angles_data)
    angles.pop(EVIDENCE_GRAPH_KEY)
    persisted.angles_data = angles
    db.commit()
    # The historical identity itself still exists, but cannot become an official
    # archived PDF without an active versioned chain, even if legacy checks pass.
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _: SimpleNamespace(is_valid=True, warnings=[], fatals=[]),
    )
    answer = client.post(
        f"/api/patients/{patient.id}/pdf",
        json={"analysis_id": study.id, "expected_revision": 1, "archive": True},
        headers=headers,
    )
    assert answer.status_code == 409
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0
    assert not list(tmp_path.glob("*.pdf"))


def test_legacy_document_pdf_route_uses_same_explicit_historical_study(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, older, _ = _case(db, dentiste)
    newer = _second(db, older)
    headers = _jwt(client, dentiste)
    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _source: SimpleNamespace(is_valid=True, warnings=[], fatals=[]),
    )
    path = f"/api/documents/patients/{patient.id}/report"
    wrong = client.post(path, json={"archive": False}, headers=headers)
    assert wrong.status_code == 422
    right = client.post(
        path,
        json={"analysis_id": older.id, "expected_revision": 1, "archive": False},
        headers=headers,
    )
    assert right.status_code == 200, right.text[:600] if right.status_code != 200 else ""
    assert right.headers["X-Cephalo-Analysis-Id"] == str(older.id)
    assert right.headers["X-Cephalo-Revision"] == "1"
    text = _compact(_text(right))
    assert _compact(f"ÉTUDE CÉPHALO ID : {older.id}") in text
    assert _compact(f"ÉTUDE CÉPHALO ID : {newer.id}") not in text
    # Old document route never archives silently.
    assert client.post(
        path, json={"analysis_id": older.id, "expected_revision": 1, "archive": True},
        headers=headers,
    ).status_code == 422
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0


def test_same_study_revision_retry_creates_exactly_one_archive_claim(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """Real JWT HTTP retry must never create a second archive for same study/revision.

    SQLite StaticPool is serial: the independent-connection race is covered by
    the separate disposable T2 HTTP CI job.
    """
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)

    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services import archive_service
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _data: SimpleNamespace(is_valid=True, fatals=[], warnings=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "isolated-archives")

    first = _request(client, patient.id, study.id, headers, revision=1, archive=True)
    assert first.status_code == 200, first.text[:500] if first.status_code != 200 else ""
    second = _request(client, patient.id, study.id, headers, revision=1, archive=True)
    assert second.status_code == 409
    assert "déjà archivé" in second.json()["detail"]

    claims = db.query(models.CephaloArchiveClaim).filter(
        models.CephaloArchiveClaim.patient_id == patient.id,
        models.CephaloArchiveClaim.analysis_id == study.id,
        models.CephaloArchiveClaim.revision == 1,
    ).all()
    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).all()
    assert len(claims) == len(docs) == 1
    assert claims[0].document_archive_id == docs[0].id
    assert docs[0].analysis_id == study.id
    assert docs[0].clinical_data["cephalo_analysis_revision"] == 1


def test_failed_atomic_archive_releases_claim(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """Failed I/O must release the claim so an approved retry can succeed."""
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)

    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    from backend.services.archive_service import ArchiveService
    from backend.services import archive_service
    monkeypatch.setattr(
        cephalo_consistency_validator, "validate",
        lambda _data: SimpleNamespace(is_valid=True, fatals=[], warnings=[]),
    )
    monkeypatch.setattr(archive_service, "ARCHIVE_BASE_DIR", tmp_path / "isolated-archives")
    original = ArchiveService.archive_document
    monkeypatch.setattr(
        ArchiveService, "archive_document",
        lambda self, **kwargs: (_ for _ in ()).throw(OSError("synthetic storage refusal")),
    )
    failed = _request(client, patient.id, study.id, headers, revision=1, archive=True)
    assert failed.status_code == 500
    assert db.query(models.CephaloArchiveClaim).filter(
        models.CephaloArchiveClaim.analysis_id == study.id,
    ).count() == 0

    monkeypatch.setattr(ArchiveService, "archive_document", original)
    retried = _request(client, patient.id, study.id, headers, revision=1, archive=True)
    assert retried.status_code == 200, retried.text[:500] if retried.status_code != 200 else ""
    assert db.query(models.CephaloArchiveClaim).filter(
        models.CephaloArchiveClaim.analysis_id == study.id,
    ).count() == 1


def test_db_unique_claim_two_independent_sqlite_connections_concurrently(tmp_path):
    """Two database sessions/process-equivalent connections, not shared TestClient.

    A first transaction holds a still-uncommitted claim while another independent
    connection attempts the same patient/study/revision. The database unique
    constraint must reject the second after the first commits.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import create_engine
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(
        "sqlite:///" + str(tmp_path / "atomic-claim.sqlite"),
        connect_args={"timeout": 5},
    )
    models.CephaloArchiveClaim.__table__.create(bind=engine)
    Session = sessionmaker(bind=engine)
    first_flushed = threading.Event()
    second_attempted = threading.Event()

    def first():
        with Session() as session:
            session.add(models.CephaloArchiveClaim(
                patient_id=1001, analysis_id=2001, revision=2,
            ))
            session.flush()
            first_flushed.set()
            assert second_attempted.wait(timeout=5)
            # The other connection attempts while the first transaction is
            # uncommitted; releasing the lock lets its UNIQUE check finish.
            import time
            time.sleep(0.15)
            session.commit()
            return "COMMITTED"

    def second():
        assert first_flushed.wait(timeout=5)
        with Session() as session:
            session.add(models.CephaloArchiveClaim(
                patient_id=1001, analysis_id=2001, revision=2,
            ))
            second_attempted.set()
            try:
                session.flush()
            except IntegrityError:
                session.rollback()
                return "UNIQUE_REJECTED"
            session.commit()
            return "UNSAFE_DUPLICATE"

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(first),pool.submit(second)]
        assert sorted(f.result(timeout=12) for f in futures)==[
            "COMMITTED", "UNIQUE_REJECTED",
        ]

    with Session() as session:
        assert session.query(models.CephaloArchiveClaim).filter_by(
            patient_id=1001,analysis_id=2001,revision=2,
        ).count()==1
    engine.dispose()


def test_existing_legacy_archive_prevents_reissue_without_claim(
    client, db, dentiste, monkeypatch, tmp_path,
):
    """Additive schema rollout must respect archives predating the claims table."""
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _ = _case(db, dentiste)
    headers = _jwt(client, dentiste)
    historical = models.DocumentArchive(
        patient_id=patient.id,
        analysis_id=study.id,
        document_type=models.DocumentType.RAPPORT_CEPHALO,
        filename="historical-synthetic.pdf",
        original_filename="historical-synthetic.pdf",
        file_path="static/archives/historical-synthetic.pdf",
        file_hash="synthetic-legacy-hash",
        file_size=100,
        document_group_id="legacy-synthetic-group",
        clinical_data={"cephalo_analysis_id": study.id, "cephalo_analysis_revision": 1},
    )
    db.add(historical)
    db.commit()
    answer = _request(client, patient.id, study.id, headers, revision=1, archive=True)
    assert answer.status_code == 409
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id==patient.id,
        models.DocumentArchive.document_type==models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 1
    assert db.query(models.CephaloArchiveClaim).filter(
        models.CephaloArchiveClaim.analysis_id==study.id,
    ).count() == 0
    assert not list(tmp_path.glob("*.pdf"))
