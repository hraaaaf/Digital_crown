from datetime import datetime, timedelta, timezone

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionIdentity,
    PatientCompanionInvitation,
)
from backend.routers import patient_companion_common
from backend.routers.patient_companion_common import manual_code_hash, recipient_hash, token_hash
from backend.services.firebase_patient_auth import FirebasePatientCredential


def test_patient_companion_routes_are_mounted_in_real_app(client):
    paths = {getattr(route, "path", None) for route in client.app.routes}
    assert "/api/patient-companion/activate" in paths
    assert "/api/patient-companion/me" in paths
    assert "/api/patient-companion/admin/patients/{patient_id}/invitation" in paths
    assert "/api/patient-companion/contexts/{access_id}/appointments" in paths
    assert "/api/patient-companion/contexts/{access_id}/shares" in paths


def test_firebase_activation_fails_closed_when_cabinet_license_is_inactive(client, db, monkeypatch):
    owner = models.User(
        email="inactive-companion-owner@test.local",
        hashed_password="unused-in-this-test",
        role=models.UserRole.DENTISTE,
        nom_complet="Owner Inactive",
        is_active=True,
        is_licensed=False,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    patient = models.Patient(
        numero_dossier="D-COMP-LICENSE",
        nom="Licence",
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    raw_token = "runtime-integration-token"
    invitation = PatientCompanionInvitation(
        employer_id=owner.id,
        patient_id=patient.id,
        token_hash=token_hash(raw_token),
        manual_code_hash=manual_code_hash("ABCD-EFGH-JKLM"),
        recipient_type="email",
        recipient_hash=recipient_hash("email", "patient@example.test"),
        relationship_type="SELF",
        created_by_user_id=owner.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    now = datetime.now(timezone.utc)
    monkeypatch.setattr(
        patient_companion_common,
        "verify_patient_id_token",
        lambda _token: FirebasePatientCredential(
            subject="firebase-runtime-patient",
            issued_at=now,
            expires_at=now + timedelta(hours=1),
            auth_time=now,
            verified_email="patient@example.test",
        ),
    )

    response = client.post(
        "/api/patient-companion/activate",
        headers={"Authorization": "Firebase test-id-token"},
        json={"token": raw_token},
    )

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "Licence cabinet inactive."
    db.refresh(invitation)
    assert invitation.consumed_at is None
    assert db.query(PatientCompanionIdentity).count() == 0
    assert db.query(PatientCompanionAccess).count() == 0
