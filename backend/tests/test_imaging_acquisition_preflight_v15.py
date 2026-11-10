"""LOT06-B isolated server preflight: never writes clinical assets."""
from datetime import datetime
import hashlib
import uuid

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.security import get_password_hash


def _patient(db, employer, suffix, deleted=False):
    p = models.Patient(
        numero_dossier="ACQ-" + suffix,
        nom="Fictif", prenom="Synthétique",
        date_naissance=datetime(2001, 2, 3), sexe="M",
        employer_id=employer,
        deleted_at=datetime(2026, 1, 1) if deleted else None,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _rdv(db, employer, patient_id):
    a = models.Appointment(
        employer_id=employer, patient_id=patient_id,
        datetime_start=datetime(2026, 10, 14, 10),
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _lab(client, db, dentiste, auth_headers, monkeypatch):
    monkeypatch.setenv("DC_V15_06_PREFLIGHT_LAB", "1")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DIGITALCROWN_ISOLATED_RUNTIME", "true")
    raw = "fixture-workstation-identity-only"
    row = models.WorkstationMode(
        id=str(uuid.uuid4()),
        employer_id=dentiste.id,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        default_experience="cabinet",
        display_name="Synthetic Imaging Staff",
    )
    db.add(row)
    db.commit()
    client.cookies.set("dc_workstation", raw)
    return row.id


def _proposal(workstation_id, **kw):
    p = {
        "workstation_id": workstation_id,
        "source_capture_id": "syntheticcapture123",
        "sha256": hashlib.sha256(b"synthetic-content").hexdigest(),
        "byte_size": 24,
        "mime_type": "image/png",
        "category": "PHOTO_CLINICAL",
    }
    p.update(kw)
    return p


def _post(client, auth_headers, payload):
    return client.post("/api/imaging-acquisitions/preflight", json=payload, headers=auth_headers)


def test_route_mounted_once_without_changing_existing_import(client):
    from backend.main import app
    assert sum(
        1 for route in app.routes
        if getattr(route, "path", "") == "/api/imaging-acquisitions/preflight"
        and "POST" in (getattr(route, "methods", set()) or set())
    ) == 1
    assert any(
        getattr(route, "path", "") == "/api/patients/{patient_id}/assets/import"
        for route in app.routes
    )


def test_disabled_by_default_fails_closed(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    monkeypatch.delenv("DC_V15_06_PREFLIGHT_LAB")
    r = _post(client, auth_headers, _proposal(workstation))
    assert r.status_code == 503
    assert r.json()["detail"] == "IMAGING_PREFLIGHT_DISABLED"


def test_cannot_enable_in_production_environment(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    monkeypatch.setenv("ENVIRONMENT", "production")
    r = _post(client, auth_headers, _proposal(workstation))
    assert r.status_code == 503


def test_unlinked_patient_and_no_capture_session_requires_human(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    before = db.query(ClinicalAsset).count()
    r = _post(client, auth_headers, _proposal(workstation))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "AWAITING_HUMAN_LINK"
    assert body["patient_id"] is None
    assert body["upload_permitted"] is False
    assert body["server_confirmed"] is False
    assert body["receipt_id"] is None
    assert db.query(ClinicalAsset).count() == before


def test_explicit_appointment_candidate_never_grants_auto_upload(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, "MATCH")
    appointment = _rdv(db, dentiste.id, patient.id)
    before = db.query(ClinicalAsset).count()
    r = _post(client, auth_headers, _proposal(
        workstation, patient_id=patient.id, appointment_id=appointment.id))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "STAFF_CONFIRMATION_REQUIRED"
    assert body["patient_id"] == patient.id
    assert body["appointment_id"] == appointment.id
    assert body["requires_staff_confirmation"] is True
    assert body["upload_permitted"] is False
    assert db.query(ClinicalAsset).count() == before


def test_wrong_patient_appointment_fails_closed(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    p1 = _patient(db, dentiste.id, "P1")
    p2 = _patient(db, dentiste.id, "P2")
    appt = _rdv(db, dentiste.id, p1.id)
    r = _post(client, auth_headers, _proposal(
        workstation, patient_id=p2.id, appointment_id=appt.id))
    assert r.status_code == 409
    assert r.json()["detail"] == "PATIENT_APPOINTMENT_CONFLICT"


def test_cross_tenant_patient_and_appointment_are_not_resolved(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    other = models.User(email="other-acq-fixture@cabinet.ma",
        hashed_password=get_password_hash("TestPass123!"), role="DENTISTE",
        nom_complet="Other", is_active=True, is_licensed=True)
    db.add(other)
    db.commit()
    db.refresh(other)
    patient = _patient(db, other.id, "OTHER")
    rdv = _rdv(db, other.id, patient.id)
    p = _post(client, auth_headers, _proposal(workstation, patient_id=patient.id))
    a = _post(client, auth_headers, _proposal(workstation, appointment_id=rdv.id))
    assert p.status_code == 404
    assert a.status_code == 404


def test_deleted_patient_is_not_a_candidate(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    deleted = _patient(db, dentiste.id, "DELETED", deleted=True)
    assert _post(client, auth_headers, _proposal(workstation, patient_id=deleted.id)).status_code == 404


def test_unlinked_appointment_requires_staff_without_silent_matching(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    appt = _rdv(db, dentiste.id, None)
    r = _post(client, auth_headers, _proposal(workstation, appointment_id=appt.id))
    assert r.status_code == 200
    assert r.json()["status"] == "AWAITING_HUMAN_LINK"
    assert r.json()["patient_id"] is None


def test_missing_or_wrong_workstation_cannot_preflight(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    assert _post(client, auth_headers, _proposal(str(uuid.uuid4()))).status_code == 403
    client.cookies.delete("dc_workstation")
    assert _post(client, auth_headers, _proposal(workstation)).status_code in {403, 423}


def test_cookie_only_post_is_rejected(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    r = client.post("/api/imaging-acquisitions/preflight", json=_proposal(workstation))
    assert r.status_code in {401, 403}


def test_forged_bearer_cannot_borrow_valid_access_cookie(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    # Login fixture sets a real HttpOnly access cookie; the header is deliberately fake.
    assert client.cookies.get("access_token")
    payload = _proposal(workstation)
    response = client.post(
        "/api/imaging-acquisitions/preflight",
        json=payload,
        headers={"Authorization": "Bearer forged-not-a-jwt"},
    )
    assert response.status_code == 401, response.text
    assert response.json()["detail"] == "EXPLICIT_STAFF_BEARER_MISMATCH"
    # A real matching header remains accepted in the isolated LAB.
    valid = _post(client, auth_headers, payload)
    assert valid.status_code == 200, valid.text
    assert valid.json()["upload_permitted"] is False


def test_unsupported_content_metadata_and_extra_fields_denied(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    assert _post(client, auth_headers, _proposal(workstation, mime_type="application/dicom")).status_code == 422
    assert _post(client, auth_headers, _proposal(workstation, category="RVG", mime_type="image/png")).status_code == 422
    assert _post(client, auth_headers, _proposal(workstation, extra_patient_name="do-not-trust")).status_code == 422


def test_repeated_preflight_never_creates_assets_or_receipts(client, db, dentiste, auth_headers, monkeypatch):
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    p = _patient(db, dentiste.id, "REPLAY")
    before = db.query(ClinicalAsset).count()
    results = [
        _post(client, auth_headers, _proposal(workstation, patient_id=p.id))
        for _ in range(3)
    ]
    assert all(r.status_code == 200 for r in results)
    assert all(r.json()["receipt_id"] is None and not r.json()["upload_permitted"] for r in results)
    assert db.query(ClinicalAsset).count() == before


def test_real_synthetic_hotfolder_preflight_remains_unconfirmed(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path
):
    """LOT06-B: a real encrypted LAB spool + staff preflight is NOT a transfer.

    The preflight endpoint does not authenticate a local spool/producer or
    authorize its transport; even an exact metadata match is not a receipt.
    """
    import base64
    import json

    from tools.imaging_gateway import Config, HotFolder

    fake_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91Jpz"
        "AAAAFklEQVR4nGPkEpFjYGBgYmBgYGBgAAAC5gBAXKUgWwAAAABJRU5ErkJggg=="
    )
    incoming = tmp_path / "synthetic-incoming"
    incoming.mkdir()
    source = incoming / "fixture.png"
    source.write_bytes(fake_png)
    # Exercise the actual background collector's .ready protocol, not only
    # the legacy stability-only HotFolder mode.
    source.with_name(source.name + ".ready").write_text(
        json.dumps({
            "version": 1,
            "size": len(fake_png),
            "sha256": hashlib.sha256(fake_png).hexdigest(),
        }),
        encoding="utf-8",
    )
    agent = HotFolder(Config(
        "fixturecabinet", "fixturestation",
        incoming, tmp_path / "synthetic-private", b"k" * 32,
        require_ready_manifest=True,
    ))
    assert agent.scan_once()["unstable"] == 1
    assert agent.scan_once()["staged"] == 1
    [item] = agent.items()
    assert item["state"] == "PENDING_CONFIRMATION"
    assert item["digest"] == hashlib.sha256(fake_png).hexdigest()
    assert agent.read_verified(item["id"]) == fake_png

    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, "BOUNDARY")
    appointment = _rdv(db, dentiste.id, patient.id)
    before_assets = db.query(ClinicalAsset).count()
    proposal = _proposal(
        workstation,
        source_capture_id="fixturecapture" + item["digest"][:16],
        sha256=item["digest"],
        byte_size=item["size"],
        mime_type=item["mime"],
        patient_id=patient.id,
        appointment_id=appointment.id,
    )
    for _ in range(3):
        response = _post(client, auth_headers, proposal)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "STAFF_CONFIRMATION_REQUIRED"
        assert body["patient_id"] == patient.id
        assert body["appointment_id"] == appointment.id
        assert body["requires_staff_confirmation"] is True
        assert body["upload_permitted"] is False
        assert body["server_confirmed"] is False
        assert body["receipt_id"] is None

    # The current API has no cryptographically bound source/spool session:
    # even attacker-supplied well-formed metadata must never become an ACK.
    forged_metadata = {**proposal, "sha256": "f" * 64}
    unbound = _post(client, auth_headers, forged_metadata)
    assert unbound.status_code == 200, unbound.text
    assert unbound.json()["upload_permitted"] is False
    assert unbound.json()["server_confirmed"] is False
    assert unbound.json()["receipt_id"] is None

    assert db.query(ClinicalAsset).count() == before_assets
    assert agent.items() == [item]
    assert agent.audit(item["id"]) == ["PENDING_CONFIRMATION"]
    assert agent.read_verified(item["id"]) == fake_png
    assert source.read_bytes() == fake_png


def test_staff_preflight_never_authorizes_spoofed_device_capture_web_import(
    client, db, dentiste, auth_headers, monkeypatch, tmp_path
):
    """LOT06-B 1+2+3: preflight metadata is not provenance or an import ticket.

    Two forged WEB_API retries must create neither an asset nor any receipt/blob.
    A genuine enrolled-device transport is not implemented by this test.
    """
    from io import BytesIO
    from PIL import Image

    monkeypatch.setattr(
        "backend.services.clinical_asset_storage.get_media_root", lambda: tmp_path
    )
    workstation = _lab(client, db, dentiste, auth_headers, monkeypatch)
    patient = _patient(db, dentiste.id, "UNTRUSTED-DEVICE")
    proposal = _post(client, auth_headers, _proposal(workstation, patient_id=patient.id))
    assert proposal.status_code == 200, proposal.text
    assert proposal.json()["requires_staff_confirmation"] is True
    assert proposal.json()["upload_permitted"] is False
    assert proposal.json()["receipt_id"] is None

    image = Image.new("RGB", (2, 2), (25, 45, 65))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    payload = buffer.getvalue()
    before = db.query(ClinicalAsset).count()
    for source_kind in ("DEVICE_CAPTURE", "device_capture"):
        response = client.post(
            f"/api/patients/{patient.id}/assets/import",
            headers=auth_headers,
            data={
                "asset_type": "PHOTO",
                "source_kind": source_kind,
                "source_ref": "FAKE_ENROLLED_DEVICE_REFERENCE",
            },
            files={"file": ("synthetic.png", payload, "image/png")},
        )
        assert response.status_code == 422, response.text
        assert response.json()["detail"] == "DEVICE_CAPTURE_REQUIRES_ENROLLED_DEVICE"
        assert db.query(ClinicalAsset).count() == before
    assert list(tmp_path.rglob("*.dcm")) == []
