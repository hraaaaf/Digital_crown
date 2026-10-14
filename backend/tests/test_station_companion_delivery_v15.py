"""04.5: fail-closed Station kiosk; only authenticated, paired phone gets PDF."""
from datetime import datetime, timedelta
import hashlib

from backend import models
from backend.models_patient_companion import PatientCompanionAccess
from backend.tests.test_station_patient_session_v15 import _station, _patient_context
from backend.tests.test_station_document_handoff_v15 import _claim
from backend.tests.test_station_care_sheet_v15 import _care_sheet, _set_mode


def _ready(client, db, dentiste, name="PHONE-READY"):
    staff, station_id = _station(client, dentiste)
    patient, access, phone = _patient_context(db, dentiste, dossier=name)
    doc = _care_sheet(db, patient)
    _set_mode(client, staff, "cabinet")
    assert client.post(
        f"/api/workstation/documents/care-sheet/{doc.id}/authorize-withdrawal",
        headers=staff,
    ).status_code == 200
    _set_mode(client, staff, "station")
    created = client.post("/api/workstation/patient-session", headers=staff)
    assert created.status_code == 201
    result = created.json()
    assert _claim(client, result, phone, access).status_code == 200
    return staff, station_id, patient, access, phone, doc, result


def _url(created, access, doc_id):
    sid = created["sessionId"]
    return f"/api/patient-companion/station-session/{sid}/documents/care-sheet/{doc_id}?accessId={access.public_id}"


def _list(created, access):
    sid = created["sessionId"]
    return f"/api/patient-companion/station-session/{sid}/documents?accessId={access.public_id}"


def test_045_personal_companion_pdf_and_kiosk_forbidden(client, db, dentiste):
    staff, _, _, access, phone, doc, created = _ready(client, db, dentiste)
    kiosk = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}/documents/care-sheet/{doc.id}",
        headers=staff,
    )
    assert kiosk.status_code == 423 and kiosk.json()["detail"] == "STATION_PDF_REQUIRES_PERSONAL_COMPANION"
    assert kiosk.headers.get("content-type", "").split(";")[0] != "application/pdf"
    listing = client.get(_list(created, access), headers=phone)
    assert listing.status_code == 200, listing.text
    assert listing.json() == {"documents": [{"documentId": doc.id, "kind": "care_sheet"}]}
    assert listing.headers.get("cache-control") == "no-store"
    pdf = client.get(_url(created, access, doc.id), headers=phone)
    assert pdf.status_code == 200, pdf.text
    assert pdf.content.startswith(b"%PDF")
    assert hashlib.sha256(pdf.content).hexdigest() == doc.file_hash
    assert pdf.headers["cache-control"].startswith("no-store")
    assert pdf.headers["content-disposition"].startswith("attachment;")
    audits = db.query(models.AuditLog).filter(
        models.AuditLog.action == "STATION_CARE_SHEET_WITHDRAWN",
        models.AuditLog.resource_id == str(doc.id),
    ).all()
    assert len(audits) == 1
    assert "Patient Companion" in audits[0].details


def test_045_companion_refuses_other_patient_access_and_bare_station_qr(client, db, dentiste):
    _staff, _sid, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-OTHER-A",
    )
    _p2, access2, phone2 = _patient_context(db, dentiste, dossier="PHONE-OTHER-B")
    assert client.get(_url(created, access, doc.id), headers=phone2).status_code == 404
    assert client.get(_url(created, access2, doc.id), headers=phone2).status_code == 404
    raw = created["handoffUrl"].split("stationSession=", 1)[1]
    assert client.get(_url(created, access, doc.id), headers={
        "Authorization": f"Bearer {raw}",
    }).status_code in (401, 403)
    assert client.get(_url(created, access, doc.id)).status_code == 401


def test_045_phone_does_not_receive_pdf_before_practitioner_authorization(client, db, dentiste):
    staff, _ = _station(client, dentiste)
    patient, access, phone = _patient_context(db, dentiste, dossier="PHONE-NO-AUTH")
    doc = _care_sheet(db, patient)
    created = client.post("/api/workstation/patient-session", headers=staff).json()
    assert _claim(client, created, phone, access).status_code == 200
    listing = client.get(_list(created, access), headers=phone)
    assert listing.status_code == 200
    assert listing.json() == {"documents": []}
    pdf = client.get(_url(created, access, doc.id), headers=phone)
    assert pdf.status_code == 409
    assert pdf.json()["detail"] == "STATION_CARE_SHEET_NOT_ELIGIBLE"


def test_045_phone_access_rejected_after_station_revocation(client, db, dentiste):
    _staff, station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-REVOKED",
    )
    station = db.get(models.WorkstationMode, station_id)
    station.revoked_at = datetime.utcnow()
    db.commit()
    assert client.get(_list(created, access), headers=phone).status_code == 404
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 404


def test_045_phone_access_rejected_after_companion_access_revoked(client, db, dentiste):
    _staff, _station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-ACCESS-REVOKED",
    )
    row = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.id == access.id,
    ).one()
    row.revoked_at = datetime.utcnow()
    db.commit()
    assert client.get(_url(created, access, doc.id), headers=phone).status_code in (401, 403, 404)


def test_045_expired_phone_session_is_purged_and_unreadable(client, db, dentiste):
    _staff, _station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-EXPIRED",
    )
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 404
    db.expire_all()
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    assert row.purged_at is not None
    assert row.patient_id is None and row.patient_access_id is None


def test_045_station_purge_immediately_revokes_phone_pdf(client, db, dentiste):
    staff, _station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-PURGE",
    )
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 200
    assert client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/purge",
        headers=staff,
    ).status_code == 204
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 404
    assert client.get(_list(created, access), headers=phone).status_code == 404


def test_046_phone_can_revoke_pickup_session_and_clear_personal_binding(client, db, dentiste):
    _staff, _station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-REVOKE-SELF",
    )
    endpoint = f"/api/patient-companion/station-session/{created['sessionId']}/purge?accessId={access.public_id}"
    removed = client.post(endpoint, headers=phone)
    assert removed.status_code == 204, removed.text
    assert removed.headers["cache-control"] == "no-store"
    db.expire_all()
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    assert row.purged_at is not None
    assert row.patient_id is None and row.patient_access_id is None
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 404
    assert client.get(_list(created, access), headers=phone).status_code == 404
    assert client.post(endpoint, headers=phone).status_code == 404


def test_046_different_patient_cannot_revoke_phone_session(client, db, dentiste):
    _staff, _station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-REVOKE-DENY",
    )
    _p2, access2, phone2 = _patient_context(db, dentiste, dossier="PHONE-REVOKE-ALIEN")
    endpoint = f"/api/patient-companion/station-session/{created['sessionId']}/purge?accessId={access.public_id}"
    assert client.post(endpoint, headers=phone2).status_code == 404
    endpoint2 = f"/api/patient-companion/station-session/{created['sessionId']}/purge?accessId={access2.public_id}"
    assert client.post(endpoint2, headers=phone2).status_code == 404
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 200


def test_045_unpaired_station_fallback_cannot_grant_phone_download(client, db, dentiste):
    staff, _station_id, _patient, access, phone, doc, created = _ready(
        client, db, dentiste, name="PHONE-FALLBACK",
    )
    row = db.get(models.WorkstationPatientSession, created["sessionId"])
    row.patient_access_id = None
    db.commit()
    assert client.get(_url(created, access, doc.id), headers=phone).status_code == 404
