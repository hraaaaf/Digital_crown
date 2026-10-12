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
    created["_phoneHeaders"] = patient_headers
    url = f"/api/patient-companion/station-session/{created['sessionId']}/documents/care-sheet/{document.id}?accessId={access.public_id}"
    return staff, created, url


def test_046_expired_identified_session_cannot_download_authorized_pdf(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST046-EXPIRED-PDF",
    )
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    denied = client.get(url, headers=created['_phoneHeaders'])
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

    denied = client.get(url, headers=created['_phoneHeaders'])
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


def test_046_purge_still_works_after_station_to_cabinet_mode_switch(client, db, dentiste):
    staff, created, _url = _authorized_document_session(
        client, db, dentiste, "ST046-MODE-PURGE",
    )
    _set_mode(client, staff, "cabinet")
    purged = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/purge",
        headers=staff,
    )
    assert purged.status_code == 204, purged.text
    db.expire_all()
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    assert row.purged_at is not None
    assert row.patient_id is None
    assert row.patient_access_id is None


def test_046_purge_still_works_after_station_revocation(client, db, dentiste):
    staff, created, _url = _authorized_document_session(
        client, db, dentiste, "ST046-REVOKED-PURGE",
    )
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    workstation = db.get(models.WorkstationMode, row.workstation_id)
    workstation.revoked_at = datetime.utcnow()
    db.commit()
    purged = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/purge",
        headers=staff,
    )
    assert purged.status_code == 204, purged.text
    db.expire_all()
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    assert row.purged_at is not None
    assert row.patient_id is None


def test_045_two_role_sender_receiver_pdf_bytes_and_purge(client, db, dentiste):
    """Two authenticated roles against one real FastAPI app: cabinet sender and station receiver.

    This is a transport-level simulation, not yet two browser processes or physical workstations.
    """
    import hashlib
    from backend.services.station_care_sheet import verified_care_sheet_bytes

    staff, workstation_id = _station(client, dentiste)
    patient, access, companion_headers = _patient_context(
        db, dentiste, dossier="ST045-SENDER-RECEIVER",
    )
    document = _care_sheet(db, patient)
    expected_pdf = verified_care_sheet_bytes(document)
    expected_hash = hashlib.sha256(expected_pdf).hexdigest()
    assert expected_pdf.startswith(b"%PDF")
    assert expected_hash == document.file_hash

    # Sender: cabinet explicitly authorizes the exact PDF.
    _set_mode(client, staff, "cabinet")
    authorized = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=staff,
    )
    assert authorized.status_code == 200, authorized.text

    # Receiver: station creates a session; companion independently claims it.
    _set_mode(client, staff, "station")
    created_response = client.post("/api/workstation/patient-session", headers=staff)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    assert _claim(client, created, companion_headers, access).status_code == 200

    url = (
        f"/api/patient-companion/station-session/{created['sessionId']}"
        f"/documents/care-sheet/{document.id}?accessId={access.public_id}"
    )
    station_refused = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}/documents/care-sheet/{document.id}",
        headers=staff,
    )
    assert station_refused.status_code == 423
    received = client.get(url, headers=companion_headers)
    assert received.status_code == 200, received.text
    assert received.headers["content-type"].startswith("application/pdf")
    assert "no-store" in received.headers["cache-control"]
    assert received.content == expected_pdf
    assert hashlib.sha256(received.content).hexdigest() == expected_hash

    # Receiver closes session: same document becomes inaccessible.
    purge = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/purge",
        headers=staff,
    )
    assert purge.status_code == 204, purge.text
    denied = client.get(url, headers=companion_headers)
    assert denied.status_code in (404, 409), denied.text
    assert denied.headers.get("content-type", "").split(";")[0] != "application/pdf"


def test_045_station_lists_only_authorized_patient_documents(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST045-DISCOVERY",
    )
    document_id = int(url.rsplit("/", 1)[1].split("?", 1)[0])
    endpoint = f"/api/workstation/patient-session/{created['sessionId']}/documents"
    result = client.get(endpoint, headers=staff)
    assert result.status_code == 200, result.text
    assert result.headers["cache-control"] == "no-store"
    assert result.json() == {"documents": [{"documentId": document_id, "kind": "care_sheet"}]}
    assert client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/purge", headers=staff,
    ).status_code == 204
    denied = client.get(endpoint, headers=staff)
    assert denied.status_code in (404, 409), denied.text


def test_045_unidentified_station_cannot_discover_documents(client, db, dentiste):
    staff, _ = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=staff)
    assert created.status_code == 201, created.text
    endpoint = f"/api/workstation/patient-session/{created.json()['sessionId']}/documents"
    denied = client.get(endpoint, headers=staff)
    assert denied.status_code == 409, denied.text
    assert denied.json()["detail"] == "STATION_PATIENT_NOT_IDENTIFIED"



def test_046_station_purge_audit_is_atomic_and_idempotent(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST046-STATION-AUDIT",
    )
    sid = created["sessionId"]
    endpoint = f"/api/workstation/patient-session/{sid}/purge"
    assert client.post(endpoint, headers=staff).status_code == 204
    db.expire_all()
    row = db.get(models.WorkstationPatientSession, sid)
    assert row.purged_at is not None
    assert row.patient_id is None and row.patient_access_id is None
    audits = db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_DOCUMENT_SESSION_PURGED_STATION",
        models.AuditLog.resource_id == sid,
    ).all()
    assert len(audits) == 1
    assert audits[0].details == "patient_binding_cleared=true;actor=station_cookie"
    assert client.get(url, headers=created["_phoneHeaders"]).status_code == 404
    assert client.post(endpoint, headers=staff).status_code == 204
    assert db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_DOCUMENT_SESSION_PURGED_STATION",
        models.AuditLog.resource_id == sid,
    ).count() == 1


def test_046_phone_purge_audit_and_download_log_minimize_identity(client, db, dentiste):
    staff, created, url = _authorized_document_session(
        client, db, dentiste, "ST046-PHONE-AUDIT",
    )
    sid = created["sessionId"]
    document_id = url.split("/care-sheet/", 1)[1].split("?", 1)[0]
    received = client.get(url, headers=created["_phoneHeaders"])
    assert received.status_code == 200
    withdrawal = db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_CARE_SHEET_WITHDRAWN",
        models.AuditLog.resource_id == document_id,
    ).one()
    assert "Patient Companion" in withdrawal.details
    assert "patient_id=" not in withdrawal.details
    assert "access_id=" not in withdrawal.details
    endpoint = (
        f"/api/patient-companion/station-session/{sid}/purge?"
        f"{url.split('?', 1)[1]}"
    )
    assert client.post(endpoint, headers=created["_phoneHeaders"]).status_code == 204
    db.expire_all()
    row = db.get(models.WorkstationPatientSession, sid)
    assert row.purged_at is not None
    assert row.patient_id is None and row.patient_access_id is None
    audits = db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_DOCUMENT_SESSION_PURGED_PHONE",
        models.AuditLog.resource_id == sid,
    ).all()
    assert len(audits) == 1
    assert audits[0].details == "patient_binding_cleared=true;actor=authenticated_companion"
    assert client.get(url, headers=created["_phoneHeaders"]).status_code == 404
    assert client.post(endpoint, headers=created["_phoneHeaders"]).status_code == 404
    assert db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_DOCUMENT_SESSION_PURGED_PHONE",
        models.AuditLog.resource_id == sid,
    ).count() == 1
