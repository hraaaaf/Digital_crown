"""J5 same-viewport A4 BEFORE/AFTER proof, synthetic only.

Both PDFs use the same verified patient/study/medical source and are rasterized
at identical A4 page geometry and zoom. The descriptive AFTER must contain no
diagnosis/treatment; archived AFTER bytes must match exactly what was previewed.
Physical printers and real patient records are strictly out of scope (LOT10).
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

import fitz
import pytest

from backend import models
from backend.tests.test_ceph_a4_descriptive_approval_v1 import (
    _environment, _cabinet, _calibrated_case, _prepare,
)


def _page_pixels(pdf: bytes, out: Path, *, title: str) -> tuple[int, int, bytes]:
    with fitz.open(stream=pdf, filetype="pdf") as doc:
        assert doc.page_count >= 1
        page = doc[0]
        assert round(page.rect.width) == 595
        assert round(page.rect.height) == 842
        pix = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        out.parent.mkdir(parents=True, exist_ok=True)
        pix.save(out)
        return pix.width, pix.height, pix.samples


def test_same_page_geometry_before_draft_after_descriptive_and_archive_byte_identity(
    client, db, dentiste, monkeypatch, tmp_path,
):
    _environment(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _points, headers = _calibrated_case(client, db, dentiste)
    revision, candidate_response = _prepare(client, patient, study, headers)
    assert candidate_response.status_code == 200, candidate_response.text[:500]
    candidate = candidate_response.json()
    after_pdf = base64.b64decode(candidate["pdf_base64"], validate=True)
    before = client.post(
        f"/api/patients/{patient.id}/pdf",
        json={"analysis_id": study.id, "expected_revision": revision, "archive": False},
        headers=headers,
    )
    assert before.status_code == 200, before.text[:500] if before.status_code != 200 else ""
    before_pdf = before.content
    assert hashlib.sha256(after_pdf).hexdigest() == candidate["pdf_sha256"]
    # BEFORE = unapproved four-part A4 working draft.
    with fitz.open(stream=before_pdf, filetype="pdf") as pdf:
        before_text = "\n".join(p.get_text() for p in pdf).upper()
    # AFTER = exact document the practitioner will explicitly approve.
    with fitz.open(stream=after_pdf, filetype="pdf") as pdf:
        after_text = "\n".join(p.get_text() for p in pdf).upper()
    assert "BROUILLON" in before_text
    assert "DIAGNOSTIC FINAL" in before_text
    assert "PLAN DE TRAITEMENT" in before_text
    assert "DESCRIPTIF" in after_text
    assert "BROUILLON" not in after_text
    assert "DIAGNOSTIC FINAL" not in after_text
    assert "PLAN DE TRAITEMENT" not in after_text
    assert "DR. TEST" in after_text
    assert "SYNTHETIC P2BIS ONLY" in after_text
    assert "ÉTUDE" in after_text.upper() or "ETUDE" in after_text.upper()
    # Save only synthetic proofs. Run artifacts are uploaded by CI; all local
    # PDF temp files outside ArchiveService are deleted by the test harness.
    proof = Path(os.environ.get("CEPH_A4_J5_SYNTHETIC_PROOF_DIR", str(tmp_path / "proof")))
    before_image = proof / "before-a4-draft-page1.png"
    after_image = proof / "after-a4-descriptive-page1.png"
    b_w, b_h, b_pixels = _page_pixels(before_pdf, before_image, title="BEFORE")
    a_w, a_h, a_pixels = _page_pixels(after_pdf, after_image, title="AFTER")
    assert (b_w, b_h) == (a_w, a_h), "Same viewport / same A4 scale required"
    assert b_pixels != a_pixels, "AFTER must visibly differ from the draft"
    # The visual captures alone do not authorize official clinical release.
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO
    ).count() == 0
    saved = client.post(
        f"/api/patients/{patient.id}/cephalo-a4/archive",
        json={
            "analysis_id": study.id, "expected_revision": revision,
            "approval_token": candidate["approval_token"],
            "pdf_base64": candidate["pdf_base64"], "approved": True,
        },
        headers=headers,
    )
    assert saved.status_code == 200, saved.text[:500] if saved.status_code != 200 else ""
    assert saved.content == after_pdf, "Archived PDF must equal AFTER preview bytes"
    (proof / "proof.txt").write_text(
        "SYNTHETIC ONLY - NO CLINICAL RELEASE\n"
        f"HEAD={os.environ.get('PRODUCT_HEAD', 'local')}\n"
        f"BEFORE_SHA256={hashlib.sha256(before_pdf).hexdigest()}\n"
        f"AFTER_SHA256={hashlib.sha256(after_pdf).hexdigest()}\n"
        f"SAME_FIRST_PAGE_RASTER={b_w}x{b_h}\n"
        "DIAGNOSIS=false\nTREATMENT=false\nARCHIVE_BYTES_EQUAL_PREVIEW=true\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize("changed_field", ["patient_nom", "patient_birth", "cabinet_name"])
def test_a4_approval_rejects_rendered_identity_changed_after_preview(
    client, db, dentiste, monkeypatch, tmp_path, changed_field,
):
    """An exact PDF may still be stale if the patient/cabinet identity changed.

    The cephalometric scientific revision remains the same. Approval must refuse
    this independent document-context mutation before any disk/SQL archive.
    """
    _environment(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, study, _points, headers = _calibrated_case(client, db, dentiste)
    revision, prepared = _prepare(client, patient, study, headers)
    assert prepared.status_code == 200, prepared.text[:450]
    candidate = prepared.json()
    if changed_field == "patient_nom":
        patient.nom = "SYNTHETIC-CHANGED-J5"
    elif changed_field == "patient_birth":
        from datetime import datetime
        patient.date_naissance = datetime(1999, 1, 1)
    else:
        config = db.query(models.CabinetConfig).filter(
            models.CabinetConfig.owner_id == dentiste.id
        ).one()
        config.nom_cabinet = "SYNTHETIC NEW CABINET NAME"
    db.commit()
    # Persisted typed-science revision itself did not move.
    db.refresh(study)
    assert study.angles_data["_evidence_graph_v1"]["revision"] == revision
    denied = client.post(
        f"/api/patients/{patient.id}/cephalo-a4/archive",
        json={
            "analysis_id": study.id, "expected_revision": revision,
            "approval_token": candidate["approval_token"],
            "pdf_base64": candidate["pdf_base64"], "approved": True,
        },
        headers=headers,
    )
    assert denied.status_code == 409
    assert db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient.id,
        models.DocumentArchive.document_type == models.DocumentType.RAPPORT_CEPHALO,
    ).count() == 0
    assert not list((tmp_path / "archives").rglob("*.pdf"))
