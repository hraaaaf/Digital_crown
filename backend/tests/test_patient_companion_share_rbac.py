from datetime import datetime

from backend import models
from backend.models_patient_companion import PatientCompanionShareGrant
from backend.security import get_password_hash


def test_secretary_cannot_share_prescription_without_prescription_permission(client, db, dentiste):
    secretary = models.User(
        email="secretary-companion@test.local",
        hashed_password=get_password_hash("TestPass123!"),
        role="SECRETAIRE",
        nom_complet="Secrétaire Test",
        is_active=True,
        is_licensed=True,
        employer_id=dentiste.id,
        permissions={"patients": True, "prescriptions": False},
    )
    db.add(secretary)
    db.commit()
    db.refresh(secretary)

    patient = models.Patient(
        numero_dossier="D-COMP-RBAC",
        nom="RBAC",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

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

    login = client.post(
        "/api/auth/login",
        data={"username": secretary.email, "password": "TestPass123!"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        f"/api/patient-companion/admin/patients/{patient.id}/shares",
        headers=headers,
        json={"resource_type": "document", "resource_id": document.id},
    )
    assert response.status_code == 403, response.text
    assert db.query(PatientCompanionShareGrant).count() == 0
