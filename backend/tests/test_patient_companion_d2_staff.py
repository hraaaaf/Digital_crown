from __future__ import annotations

import uuid
from datetime import datetime

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import PatientCompanionInvitation
from backend.security import get_password_hash


def _owner(db, email: str):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr D2",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _patient(db, owner, nom: str):
    patient = models.Patient(
        numero_dossier=f"D2-{uuid.uuid4().hex[:8]}",
        nom=nom,
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def _headers(client, owner):
    response = client.post(
        "/api/auth/login",
        data={"username": owner.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_staff_status_is_read_only_safe_projection_and_qr_is_ephemeral(client, db):
    owner = _owner(db, "d2-owner@test.local")
    patient = _patient(db, owner, "D2")
    headers = _headers(client, owner)

    invitation = client.post(
        f"/api/patient-companion/admin/patients/{patient.id}/invitation",
        headers=headers,
        json={"recipient_type": "email", "recipient": "patient@example.test"},
    )
    assert invitation.status_code == 201, invitation.text
    payload = invitation.json()
    assert payload["qr_data_url"].startswith("data:image/png;base64,")
    assert payload["qr_token"] not in payload["qr_data_url"]

    media = ClinicalAsset(
        employer_id=owner.id,
        patient_id=patient.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
        mime_type="image/jpeg",
        created_by=owner.id,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    grant = client.post(
        f"/api/patient-companion/admin/patients/{patient.id}/shares",
        headers=headers,
        json={"resource_type": "media", "resource_id": media.id},
    )
    assert grant.status_code == 201, grant.text

    status = client.get(
        f"/api/patient-companion/admin/patients/{patient.id}/status",
        headers=headers,
    )
    assert status.status_code == 200, status.text
    assert status.headers["cache-control"] == "no-store"
    body = status.json()
    assert body["patient_id"] == patient.id
    assert body["pending_invitation"]["invitation_id"] == payload["invitation_id"]
    assert body["shares"][0]["resource_id"] == media.id
    serialized = status.text
    assert "token_hash" not in serialized
    assert "manual_code_hash" not in serialized
    assert "recipient_hash" not in serialized
    assert payload["qr_token"] not in serialized
    assert payload["manual_code"] not in serialized

    row = db.query(PatientCompanionInvitation).filter_by(public_id=payload["invitation_id"]).one()
    assert row.token_hash != payload["qr_token"]
    assert row.manual_code_hash not in serialized


def test_staff_status_is_tenant_scoped(client, db):
    owner_a = _owner(db, "d2-a@test.local")
    owner_b = _owner(db, "d2-b@test.local")
    patient_b = _patient(db, owner_b, "Tenant-B")
    headers_a = _headers(client, owner_a)
    response = client.get(
        f"/api/patient-companion/admin/patients/{patient_b.id}/status",
        headers=headers_a,
    )
    assert response.status_code == 404
