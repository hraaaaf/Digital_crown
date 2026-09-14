from datetime import datetime

from backend import models
from backend.models_patient_companion import PatientCompanionShareGrant
from backend.security import get_password_hash


def _secretary(db, owner):
    user = models.User(
        email="secretary-companion@test.local",
        hashed_password=get_password_hash("TestPass123!"),
        role="SECRETAIRE",
        nom_complet="Secrétaire Test",
        is_active=True,
        is_licensed=True,
        employer_id=owner.id,
        permissions={
            "patients": True,
            "prescriptions": True,
            "accounting": True,
            "clinical": True,
        },
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client, user):
    login = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _patient(db, owner, dossier):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="RBAC",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_secretary_cannot_issue_companion_invitation_even_with_patient_access(client, db, dentiste):
    secretary = _secretary(db, dentiste)
    patient = _patient(db, dentiste, "D-COMP-ADMIN")

    response = client.post(
        f"/api/patient-companion/admin/patients/{patient.id}/invitation",
        headers=_headers(client, secretary),
        json={"recipient_type": "email", "recipient": "patient@example.test"},
    )
    assert response.status_code == 403, response.text


def test_secretary_cannot_publish_patient_share_even_with_document_rights(client, db, dentiste):
    secretary = _secretary(db, dentiste)
    patient = _patient(db, dentiste, "D-COMP-RBAC")

    document = models.DocumentArchive(
        patient_id=patient.id,
        uploaded_by_id=dentiste.id,
        document_type=models.DocumentType.ORDONNANCE,
        filename="ordonnance.pdf",
        original_filename="ordonnance.pdf",
        document_group_id="companion-rbac",
        version_number=1,
        is_latest_version=True,
        file_hash="a" * 64,
        file_size=128,
        file_path="documents/ordonnance.pdf",
        status=models.DocumentStatus.ACTIF,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    response = client.post(
        f"/api/patient-companion/admin/patients/{patient.id}/shares",
        headers=_headers(client, secretary),
        json={"resource_type": "document", "resource_id": document.id},
    )
    assert response.status_code == 403, response.text
    assert db.query(PatientCompanionShareGrant).count() == 0
