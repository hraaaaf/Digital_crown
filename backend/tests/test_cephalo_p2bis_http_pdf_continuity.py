"""P2bis: nonpatient real HTTP JWT GET -> landmark PUT -> GET -> PDF bytes.

All writes remain in StaticPool isolated SQLite and in a pytest tmp_path.
This does not pretend to cover browser UI or clinical approval.
"""
from __future__ import annotations

from copy import deepcopy

import fitz

from backend import models
from backend.tests.test_cephalo_r23g5_authenticated_api import (
    _case, _jwt, _read, PATH,
)
from backend.tests.conftest import make_user
from backend.routers.documents import doc_factory
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY

_PROFILE_COUNTS = {"mcnamara": 13, "ricketts_atlas2009": 33, "ricketts_gregoret13": 13}


def _compact(value: str) -> str:
    # PDF parsers may insert whitespace/line wraps inside canonical IDs.
    return "".join(ch for ch in value if ch.isalnum())


def _cabinet(db, dentist):
    db.add(models.CabinetConfig(
        owner_id=dentist.id, nom_cabinet="SYNTHETIC P2BIS ONLY",
        nom_praticien="NON PATIENT",
    ))
    db.commit()


def _temporary_pdf_output(monkeypatch, tmp_path):
    # Globally constructed document factory must never write to an actual
    # cabinet's document store when this HTTP contract executes.
    monkeypatch.setattr(doc_factory.ceph_gen, "output_dir", str(tmp_path))
    monkeypatch.setattr(doc_factory, "output_dir", str(tmp_path))


def test_real_jwt_get_put_get_pdf_preserves_59_canonical_ids(
    client, db, dentiste, tmp_path, monkeypatch
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, analysis, points = _case(db, dentiste)
    headers = _jwt(client, dentiste)

    _, initial = _read(client, analysis.id, headers)
    assert initial["revision"] == 1

    edited = deepcopy(points)
    next(p for p in edited if p["id"] == "A")["x"] += 2
    update = client.put(PATH + str(analysis.id), json={"landmarks": edited}, headers=headers)
    assert update.status_code == 200, update.text[:600]
    after, scientific = _read(client, analysis.id, headers)
    assert scientific["revision"] == 2
    assert after["landmarks_data"] == edited

    expected = set()
    total_profile_rows = 0
    for slot, count in _PROFILE_COUNTS.items():
        profile = scientific["protocol_profiles"][slot]
        assert len(profile["rows"]) == count
        total_profile_rows += len(profile["rows"])
        expected.update(row["canonical_measurement_id"] for row in profile["rows"])
        assert all(row["classification_authority"] is False for row in profile["rows"])
        assert all(
            row["value"] is None for row in profile["rows"]
            if row["availability_status"] != "AVAILABLE"
        )
    # Versioned protocols may legitimately share a canonical measurement ID;
    # 59 is the total factor rows, not necessarily the number of unique IDs.
    assert total_profile_rows == sum(_PROFILE_COUNTS.values())
    assert expected

    response = client.post(f"/api/patients/{patient.id}/pdf", json={"analysis_id": analysis.id, "expected_revision": scientific["revision"], "archive": False}, headers=headers)
    assert response.status_code == 200, response.text[:600] if response.status_code != 200 else ""
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")

    with fitz.open(stream=response.content, filetype="pdf") as doc:
        assert len(doc) >= 2
        rendered = "\n".join(page.get_text() for page in doc)
    normalized = _compact(rendered)
    for canonical_id in expected:
        assert _compact(canonical_id) in normalized, canonical_id
    assert "DOCUMENT CLINIQUE INCOMPLET" in rendered or "INCOMPLETE" in rendered
    assert "SYNTHETIC" in rendered
    assert len(list(tmp_path.glob("*.pdf"))) == 1


def test_report_http_denies_unauthorized_tenant_and_stale_data(
    client, db, dentiste, tmp_path, monkeypatch
):
    _temporary_pdf_output(monkeypatch, tmp_path)
    _cabinet(db, dentiste)
    patient, analysis, points = _case(db, dentiste)

    # Absence of JWT never creates a document.
    client.cookies.clear()
    guest = client.post(f"/api/patients/{patient.id}/pdf", json={"analysis_id": analysis.id, "expected_revision": 1, "archive": False})
    assert guest.status_code == 401
    assert list(tmp_path.glob("*.pdf")) == []

    outsider = make_user(db, email="p2bis-other-cabinet@cabinet.invalid")
    unauthorized = client.post(
        f"/api/patients/{patient.id}/pdf", json={"analysis_id": analysis.id, "expected_revision": 1, "archive": False},
        headers=_jwt(client, outsider),
    )
    assert unauthorized.status_code == 403
    assert list(tmp_path.glob("*.pdf")) == []

    # Deliberately corrupt synthetic typed evidence in test DB only.
    persisted = db.get(models.CephaloAnalysis, analysis.id)
    corrupted = deepcopy(persisted.angles_data)
    corrupted[EVIDENCE_GRAPH_KEY]["current_landmark_refs"] = []
    persisted.angles_data = corrupted
    db.commit()
    db.expire_all()

    original_owner_headers = _jwt(client, dentiste)
    broken_read = client.get(PATH + str(analysis.id), headers=original_owner_headers)
    assert broken_read.status_code == 409

    draft = client.post(
        f"/api/patients/{patient.id}/pdf", json={"analysis_id": analysis.id, "expected_revision": 1, "archive": False},
        headers=original_owner_headers,
    )
    # A safe, incomplete draft is allowed; a clinically authoritative
    # document from stale evidence is never allowed.
    if draft.status_code == 200:
        with fitz.open(stream=draft.content, filetype="pdf") as doc:
            rendered = "\n".join(page.get_text() for page in doc)
        assert "DOCUMENT CLINIQUE INCOMPLET" in rendered or "INCOMPLETE" in rendered
        assert "Analyse protocolaire" not in rendered or "Profil non vérifié" in rendered
    else:
        assert draft.status_code in (409, 422)
