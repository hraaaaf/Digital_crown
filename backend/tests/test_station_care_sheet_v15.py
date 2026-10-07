from datetime import datetime

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.patient_companion_common import create_patient_device_token
from backend.services.archive_service import ArchiveService


def _login(client, email: str, password: str = "TestPass123!") -> dict[str, str]:
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return {"Authorization": f"Bearer {token}"}


def _station(client, owner) -> dict[str, str]:
    headers = _login(client, owner.email)
    assert client.get("/api/workstation/state", headers=headers).status_code == 200
    assert client.post(
        "/api/workstation/owner-pin",
        headers=headers,
        json={"accountPassword": "TestPass123!", "newPin": "2468"},
    ).status_code == 200
    mode = client.post(
        "/api/workstation/mode",
        headers=headers,
        json={"mode": "station", "ownerPin": "2468"},
    )
    assert mode.status_code == 200, mode.text
    return headers


def _identified_session(client, db, owner, *, dossier: str = "ST043-001"):
    headers = _station(client, owner)
    created = client.post("/api/workstation/patient-session", headers=headers)
    assert created.status_code == 201, created.text
    session = created.json()
    raw = session["handoffUrl"].split("stationSession=", 1)[1]

    patient = models.Patient(
        numero_dossier=dossier,
        nom="Station",
        prenom="Care",
        date_naissance=datetime(1990, 1, 1),
        sexe="F",
        employer_id=owner.id,
    )
    db.add(patient)
    db.flush()
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{dossier}",
        last_seen_at=datetime.utcnow(),
    )
    db.add(identity)
    db.flush()
    access = PatientCompanionAccess(
        identity_id=identity.id,
        employer_id=owner.id,
        patient_id=patient.id,
        relationship_type="SELF",
    )
    db.add(access)
    db.commit()
    db.refresh(access)

    patient_headers = {
        "Authorization": f"Bearer {create_patient_device_token(identity, access)}"
    }
    claimed = client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": raw, "accessId": access.public_id},
    )
    assert claimed.status_code == 200, claimed.text
    return headers, session["sessionId"], patient


def _care_sheet(db, patient, *, status: str = "VALIDATED"):
    document, _ = ArchiveService(db).archive_document(
        patient_id=patient.id,
        file_content=b"%PDF-1.4\n% station care sheet\n%%EOF\n",
        filename=f"Feuille_soins_CNSS_{patient.id}.pdf",
        doc_type=models.DocumentType.AUTRE,
        title="Feuille de soins CNSS",
        tags=["insurance_submission", "cnss"],
        clinical_data={
            "kind": "INSURANCE_SUBMISSION",
            "schema_version": "1",
            "draft": {"status": status},
        },
        is_accounted=False,
        is_collected=False,
        payment_status=models.PaiementStatut.EN_ATTENTE,
    )
    return document


def test_station_care_sheet_requires_explicit_withdrawal_authorization(client, db, dentiste):
    headers, session_id, patient = _identified_session(client, db, dentiste)
    document = _care_sheet(db, patient)

    denied = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_CARE_SHEET_NOT_ELIGIBLE"

    authorized = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert authorized.status_code == 200, authorized.text
    assert authorized.json() == {
        "status": "AUTHORIZED",
        "documentId": document.id,
        "created": True,
    }

    downloaded = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.headers["content-type"].startswith("application/pdf")
    assert downloaded.headers["cache-control"] == "no-store"
    assert downloaded.content.startswith(b"%PDF")

    actions = {
        row.action for row in db.query(models.AuditLog).filter(
            models.AuditLog.employer_id == dentiste.id,
            models.AuditLog.resource_type == "DocumentArchive",
            models.AuditLog.resource_id == str(document.id),
        ).all()
    }
    assert "STATION_CARE_SHEET_WITHDRAWAL_AUTHORIZED" in actions
    assert "STATION_CARE_SHEET_WITHDRAWN" in actions


def test_station_care_sheet_authorization_is_idempotent(client, db, dentiste):
    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-IDEMP"
    )
    document = _care_sheet(db, patient)

    first = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    second = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["created"] is True
    assert second.status_code == 200
    assert second.json()["created"] is False


def test_station_care_sheet_refuses_non_finalized_archive(client, db, dentiste):
    headers, _session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-DRAFT"
    )
    document = _care_sheet(db, patient, status="READY_FOR_REVIEW")

    denied = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "CARE_SHEET_NOT_FINALIZED"


def test_station_care_sheet_hides_other_patient_document(client, db, dentiste):
    headers, session_id, _patient = _identified_session(
        client, db, dentiste, dossier="ST043-A"
    )
    other = models.Patient(
        numero_dossier="ST043-B",
        nom="Other",
        prenom="Patient",
        date_naissance=datetime(1985, 2, 2),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(other)
    db.commit()
    document = _care_sheet(db, other)

    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200

    hidden = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == "STATION_CARE_SHEET_NOT_FOUND"


def test_station_care_sheet_authorization_is_invalidated_by_file_replacement(client, db, dentiste):
    headers, session_id, patient = _identified_session(
        client, db, dentiste, dossier="ST043-HASH"
    )
    document = _care_sheet(db, patient)

    assert client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    ).status_code == 200

    previous_hash = document.file_hash
    ArchiveService(db)._replace_document_in_place(
        document_id=document.id,
        patient_id=patient.id,
        file_content=b"%PDF-1.4\n% replaced station care sheet\n%%EOF\n",
        filename=document.original_filename,
        doc_type=document.document_type,
        uploaded_by_id=document.uploaded_by_id,
        title=document.title,
        description=document.description,
        tags=document.tags or [],
        clinical_data=document.clinical_data,
        analysis_id=document.analysis_id,
        is_accounted=document.is_accounted,
        is_collected=document.is_collected,
        payment_status=document.payment_status,
    )
    db.refresh(document)
    assert document.file_hash != previous_hash

    denied = client.get(
        f"/api/workstation/patient-session/{session_id}/documents/care-sheet/{document.id}",
        headers=headers,
    )
    assert denied.status_code == 409
    assert denied.json()["detail"] == "STATION_CARE_SHEET_NOT_ELIGIBLE"

    renewed = client.post(
        f"/api/workstation/documents/care-sheet/{document.id}/authorize-withdrawal",
        headers=headers,
    )
    assert renewed.status_code == 200
    assert renewed.json()["created"] is True
