"""V1.5-04.4 — QR/NFC session is the station-scoped identity handoff, not a document bearer URL.

Synthetic FastAPI tests only: same opaque token underlies QR and NFC. 04.5 delivery,
printing, Pocket transfer and a distinct document download QR are deliberately absent.
"""
from datetime import datetime, timedelta
import hashlib

from backend import models
from backend.services.station_care_sheet import WITHDRAW_ACTION
from backend.tests.test_station_patient_session_v15 import _patient_context, _station, _login
from backend.tests.test_station_care_sheet_v15 import _care_sheet, _set_mode


def _claim(client, created, patient_headers, access):
    token = created["handoffUrl"].split("stationSession=", 1)[1]
    return client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": token, "accessId": access.public_id},
    )


def test_044_qr_nfc_one_shot_identification_then_exact_document_withdrawal(client, db, dentiste):
    """Replay of QR/NFC identity token fails even after authorized PDF retrieval."""
    staff, workstation_id = _station(client, dentiste)
    patient, access, patient_headers = _patient_context(
        db, dentiste, dossier="ST044-DOC-OK",
    )
    document = _care_sheet(db, patient)
    _set_mode(client, staff, "cabinet")
    approval = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=staff,
    )
    assert approval.status_code == 200, approval.text
    _set_mode(client, staff, "station")

    created_resp = client.post("/api/workstation/patient-session", headers=staff)
    assert created_resp.status_code == 201, created_resp.text
    created = created_resp.json()
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == created["sessionId"],
    ).one()
    assert row.workstation_id == workstation_id
    assert row.employer_id == dentiste.id
    assert row.patient_id is None
    assert row.patient_access_id is None
    assert created["handoffUrl"] == created["nfcPayload"]
    assert "stationSession=" in created["handoffUrl"]
    assert created["qrDataUrl"].startswith("data:image/png;base64,")
    assert created["sessionId"] not in created["handoffUrl"]

    not_identified = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}/documents/care-sheet/{document.id}",
        headers=staff,
    )
    assert not_identified.status_code == 409
    assert not_identified.json()["detail"] == "STATION_PATIENT_NOT_IDENTIFIED"

    claimed = _claim(client, created, patient_headers, access)
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["status"] == "identified"

    replay = _claim(client, created, patient_headers, access)
    assert replay.status_code == 409

    # Shared kiosk must never receive patient PDF bytes.
    station_refused = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}/documents/care-sheet/{document.id}",
        headers=staff,
    )
    assert station_refused.status_code == 423
    download = client.get(
        f"/api/patient-companion/station-session/{created['sessionId']}/documents/care-sheet/{document.id}?accessId={access.public_id}",
        headers=patient_headers,
    )
    assert download.status_code == 200, download.text
    assert "no-store" in download.headers["cache-control"]
    assert hashlib.sha256(download.content).hexdigest() == document.file_hash
    event_count = db.query(models.AuditLog).filter(
        models.AuditLog.action == WITHDRAW_ACTION,
        models.AuditLog.resource_id == str(document.id),
        models.AuditLog.employer_id == dentiste.id,
    ).count()
    assert event_count == 1


def test_044_station_revocation_invalidates_outstanding_qr_nfc_claim(client, db, dentiste):
    """Previously minted handoff cannot authenticate when station is revoked."""
    staff, workstation_id = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=staff).json()
    _patient, access, patient_headers = _patient_context(
        db, dentiste, dossier="ST044-REVOKED",
    )
    station = db.get(models.WorkstationMode, workstation_id)
    station.revoked_at = datetime.utcnow()
    db.commit()

    denied = _claim(client, created, patient_headers, access)
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_SESSION_INVALID_OR_USED"
    db.refresh(db.get(models.WorkstationPatientSession, created["sessionId"]))
    assert db.get(models.WorkstationPatientSession, created["sessionId"]).claimed_at is None


def test_044_station_mode_change_invalidates_outstanding_qr_nfc_claim(client, db, dentiste):
    """A station token is not valid after staff converts that station to cabinet mode."""
    staff, _workstation_id = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=staff).json()
    _patient, access, patient_headers = _patient_context(
        db, dentiste, dossier="ST044-MODE",
    )
    _set_mode(client, staff, "cabinet")
    denied = _claim(client, created, patient_headers, access)
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_SESSION_INVALID_OR_USED"


def test_044_replaced_or_expired_token_never_identifies_a_document_patient(client, db, dentiste):
    staff, _workstation_id = _station(client, dentiste)
    first = client.post("/api/workstation/patient-session", headers=staff).json()
    second = client.post("/api/workstation/patient-session", headers=staff).json()
    _patient, access, patient_headers = _patient_context(
        db, dentiste, dossier="ST044-REPLACED",
    )
    assert _claim(client, first, patient_headers, access).status_code == 409
    assert _claim(client, second, patient_headers, access).status_code == 200

    third = client.post("/api/workstation/patient-session", headers=staff).json()
    dbrow = db.get(models.WorkstationPatientSession, third["sessionId"])
    dbrow.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    assert _claim(client, third, patient_headers, access).status_code == 409


def test_044_host_header_poisoning_cannot_issue_qr_link(client, db, dentiste):
    """Unauthenticated Host authority may not become QR bearer destination."""
    staff, _station_id = _station(client, dentiste)
    attack_headers = {**staff, "Host": "attacker.invalid"}
    response = client.post("/api/workstation/patient-session", headers=attack_headers)
    assert response.status_code == 503, response.text
    assert response.json()["detail"] == "STATION_HANDOFF_ORIGIN_NOT_TRUSTED"
    assert db.query(models.WorkstationPatientSession).count() == 0


def test_044_configured_origin_ignores_untrusted_host(client, db, dentiste, monkeypatch):
    """Handoff QR + NFC reflect only deliberate canonical configuration."""
    from backend.config import settings as app_settings

    staff, _station_id = _station(client, dentiste)
    monkeypatch.setattr(app_settings, "STATION_HANDOFF_PUBLIC_ORIGIN", "https://cabinet.example:8005")
    response = client.post(
        "/api/workstation/patient-session", headers={**staff, "Host": "attacker.invalid"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["handoffUrl"].startswith("https://cabinet.example:8005/companion?stationSession=")
    assert data["nfcPayload"] == data["handoffUrl"]
    assert "attacker.invalid" not in data["handoffUrl"]
    assert db.query(models.WorkstationPatientSession).count() == 1


def test_044_cabinet_requires_https_non_loopback_handoff_origin(client, db, dentiste, monkeypatch):
    """Reject unsafe or absent configured origins before revoking active session."""
    from backend.config import settings as app_settings

    staff, _station_id = _station(client, dentiste)
    monkeypatch.setattr(app_settings, "ENVIRONMENT", "cabinet")
    for origin, error in [
        ("", "STATION_HANDOFF_ORIGIN_NOT_CONFIGURED"),
        ("http://cabinet.example:8005", "STATION_HANDOFF_ORIGIN_INSECURE"),
        ("https://localhost:8005", "STATION_HANDOFF_ORIGIN_INSECURE"),
        ("https://cabinet.example:8005/companion", "STATION_HANDOFF_ORIGIN_INVALID"),
        ("https://cabinet.example:invalid", "STATION_HANDOFF_ORIGIN_INVALID"),
    ]:
        monkeypatch.setattr(app_settings, "STATION_HANDOFF_PUBLIC_ORIGIN", origin)
        response = client.post("/api/workstation/patient-session", headers=staff)
        assert response.status_code == 503, (origin, response.text)
        assert response.json()["detail"] == error
        assert db.query(models.WorkstationPatientSession).count() == 0

    monkeypatch.setattr(app_settings, "STATION_HANDOFF_PUBLIC_ORIGIN", "https://cabinet.example:8005")
    allowed = client.post("/api/workstation/patient-session", headers=staff)
    assert allowed.status_code == 201, allowed.text
    assert allowed.json()["handoffUrl"].startswith("https://cabinet.example:8005/companion?stationSession=")
