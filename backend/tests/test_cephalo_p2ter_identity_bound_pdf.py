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
    return "".join(c for c in t if c.isalnum())


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
    assert no_revision.status_code == 409
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
