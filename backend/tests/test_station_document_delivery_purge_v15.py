"""04.5/04.6 red-team regression: document delivery must fail closed after session invalidation.

This is a targeted security gate, not proof of print, Pocket delivery, or physical QR scanning.
"""
from datetime import datetime, timedelta

from backend import models
from backend.tests.test_station_document_handoff_v15 import _claim
from backend.tests.test_station_patient_session_v15 import _patient_context, _station
from backend.tests.test_station_care_sheet_v15 import _care_sheet, _set_mode


def _authorized_document_session(client, db, dentiste, dossier):
    staff, _workstation_id = _station(client, dentiste)
    patient, access, patient_headers = _patient_context(db, dentiste, dossier=dossier)
    document = _care_sheet(db, patient)
    _set_mode(client, staff, "cabinet")
    approval = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=staff,
    )
    assert approval.status_code == 200, approval.text
    _set_mode(client, staff, "station")
    created_response = client.post("/api/workstation/patient-session", headers=staff)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    claimed = _claim(client, created, patient_headers, access)
    assert claimed.status_code == 200, claimed.text
    url = f"/api/workstation/patient-session/{created['sessionId']}/documents/care-sheet/{document.id}"
    return staff, created, url


def test_046_expired_identified_session_cannot_download_authorized_pdf(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST046-EXPIRED-PDF",
    )
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    denied = client.get(url, headers=staff)
    assert denied.status_code in (404, 409), denied.text
    assert denied.headers.get("content-type", "").split(";")[0] != "application/pdf"
    db.expire_all()
    assert db.get(models.WorkstationPatientSession, created["sessionId"]).patient_id is None


def test_046_purged_identified_session_cannot_download_authorized_pdf(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST046-PURGED-PDF",
    )
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    row.purged_at = datetime.utcnow()
    row.patient_id = None
    row.patient_access_id = None
    db.commit()

    denied = client.get(url, headers=staff)
    assert denied.status_code in (404, 409), denied.text
    assert denied.headers.get("content-type", "").split(";")[0] != "application/pdf"


def test_045_identity_token_is_not_a_document_download_credential(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST045-TOKEN-NOT-PDF",
    )
    token = created["handoffUrl"].split("stationSession=", 1)[1]
    assert token not in url
    assert created["nfcPayload"] == created["handoffUrl"]
    # Without workstation staff authentication, neither the URL nor bearer token grants PDF access.
    unauthenticated = client.get(url, headers={"Authorization": f"Bearer {token}"})
    assert unauthenticated.status_code in (401, 403), unauthenticated.text
    assert unauthenticated.headers.get("content-type", "").split(";")[0] != "application/pdf"
