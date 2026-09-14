from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend import models
from backend.models_media_core import ClinicalAsset
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionInvitation
from backend.routers import patient_companion_activation, patient_companion_common
from backend.security import get_password_hash
from backend.services.firebase_patient_auth import FirebasePatientAuthInvalid, FirebasePatientCredential


def _user(db, *, email: str):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Test",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _patient(db, owner, *, nom: str):
    patient = models.Patient(
        numero_dossier=f"D-{uuid.uuid4().hex[:8]}",
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


def _login(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(autouse=True)
def _fake_patient_auth(monkeypatch):
    credentials = {
        "firebase-a": FirebasePatientCredential(
            subject="firebase-subject-a",
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            auth_time=datetime.now(timezone.utc),
        ),
        "firebase-b": FirebasePatientCredential(
            subject="firebase-subject-b",
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            auth_time=datetime.now(timezone.utc),
        ),
    }

    def _verify(token: str):
        credential = credentials.get(token)
        if credential is None:
            raise FirebasePatientAuthInvalid("invalid")
        return credential

    monkeypatch.setattr(patient_companion_common, "verify_patient_id_token", _verify)
    monkeypatch.setattr(patient_companion_activation, "check_rate_limit", lambda *_args, **_kwargs: None)


def _create_invitation(client, headers, patient_id, **payload):
    response = client.post(
        f"/api/patient-companion/admin/patients/{patient_id}/invitation",
        headers=headers,
        json=payload or {},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _activate(client, firebase_token, **payload):
    client.cookies.clear()
    return client.post(
        "/api/patient-companion/activate",
        headers={"Authorization": f"Bearer {firebase_token}"},
        json=payload,
    )


def test_invitation_is_scoped_hashed_and_single_use(client, db):
    owner = _user(db, email="owner-a@test.local")
    patient = _patient(db, owner, nom="A")
    headers = _login(client, owner)

    invitation_payload = _create_invitation(client, headers, patient.id)
    raw_token = invitation_payload["qr_token"]
    manual_code = invitation_payload["manual_code"]
    row = db.query(PatientCompanionInvitation).filter_by(
        public_id=invitation_payload["invitation_id"]
    ).one()
    assert row.employer_id == owner.id
    assert row.patient_id == patient.id
    assert row.token_hash != raw_token
    assert row.manual_code_hash != manual_code.replace("-", "")

    activated = _activate(client, "firebase-a", token=raw_token)
    assert activated.status_code == 200, activated.text
    assert activated.headers["cache-control"] == "no-store"
    access_id = activated.json()["access_id"]

    replay = _activate(client, "firebase-b", token=raw_token)
    assert replay.status_code == 400
    assert db.query(PatientCompanionAccess).filter_by(public_id=access_id).count() == 1


def test_manual_code_supports_parent_access_to_multiple_patients(client, db):
    owner = _user(db, email="owner-family@test.local")
    patient_a = _patient(db, owner, nom="Child-A")
    patient_b = _patient(db, owner, nom="Child-B")
    headers = _login(client, owner)
    invite_a = _create_invitation(client, headers, patient_a.id, relationship_type="PARENT")
    invite_b = _create_invitation(client, headers, patient_b.id, relationship_type="PARENT")

    assert _activate(client, "firebase-a", manual_code=invite_a["manual_code"]).status_code == 200
    assert _activate(client, "firebase-a", manual_code=invite_b["manual_code"]).status_code == 200

    client.cookies.clear()
    me = client.get("/api/patient-companion/me", headers={"Authorization": "Bearer firebase-a"})
    assert me.status_code == 200, me.text
    contexts = me.json()["contexts"]
    assert len(contexts) == 2
    assert {context["patient"]["nom"] for context in contexts} == {"Child-A", "Child-B"}
    assert {context["relationship_type"] for context in contexts} == {"PARENT"}


def test_staff_cannot_invite_patient_from_another_tenant(client, db):
    owner_a = _user(db, email="owner-a2@test.local")
    owner_b = _user(db, email="owner-b2@test.local")
    patient_b = _patient(db, owner_b, nom="B")
    headers_a = _login(client, owner_a)
    response = client.post(
        f"/api/patient-companion/admin/patients/{patient_b.id}/invitation",
        headers=headers_a,
        json={},
    )
    assert response.status_code == 404


def test_patient_context_blocks_cross_identity_and_cross_patient_appointments(client, db):
    owner = _user(db, email="owner-appt@test.local")
    patient_a = _patient(db, owner, nom="A")
    patient_b = _patient(db, owner, nom="B")
    headers = _login(client, owner)
    invite_a = _create_invitation(client, headers, patient_a.id)
    invite_b = _create_invitation(client, headers, patient_b.id)
    activation_a = _activate(client, "firebase-a", token=invite_a["qr_token"])
    activation_b = _activate(client, "firebase-b", token=invite_b["qr_token"])
    assert activation_a.status_code == 200
    assert activation_b.status_code == 200
    access_a = activation_a.json()["access_id"]
    access_b = activation_b.json()["access_id"]

    db.add_all([
        models.Appointment(
            patient_id=patient_a.id,
            patient_name="Patient A",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            motif="A-only",
            employer_id=owner.id,
        ),
        models.Appointment(
            patient_id=patient_b.id,
            patient_name="Patient B",
            datetime_start=datetime.utcnow() + timedelta(days=1),
            duration_minutes=30,
            motif="B-only",
            employer_id=owner.id,
        ),
    ])
    db.commit()

    client.cookies.clear()
    own = client.get(
        f"/api/patient-companion/contexts/{access_a}/appointments",
        headers={"Authorization": "Bearer firebase-a"},
    )
    assert own.status_code == 200, own.text
    assert [item["motif"] for item in own.json()["items"]] == ["A-only"]
    cross = client.get(
        f"/api/patient-companion/contexts/{access_b}/appointments",
        headers={"Authorization": "Bearer firebase-a"},
    )
    assert cross.status_code == 404


def test_patient_share_state_is_explicit_and_patient_scoped(client, db):
    owner = _user(db, email="owner-share@test.local")
    patient_a = _patient(db, owner, nom="Share-A")
    patient_b = _patient(db, owner, nom="Share-B")
    headers = _login(client, owner)
    media_a = ClinicalAsset(
        employer_id=owner.id,
        patient_id=patient_a.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
        mime_type="image/jpeg",
        created_by=owner.id,
    )
    media_b = ClinicalAsset(
        employer_id=owner.id,
        patient_id=patient_b.id,
        asset_type="PHOTO",
        source_kind="UPLOAD",
        mime_type="image/jpeg",
        created_by=owner.id,
    )
    db.add_all([media_a, media_b])
    db.commit()
    db.refresh(media_a)
    db.refresh(media_b)

    invite = _create_invitation(client, headers, patient_a.id)
    activation = _activate(client, "firebase-a", token=invite["qr_token"])
    access_a = activation.json()["access_id"]
    wrong = client.post(
        f"/api/patient-companion/admin/patients/{patient_a.id}/shares",
        headers=headers,
        json={"resource_type": "media", "resource_id": media_b.id},
    )
    assert wrong.status_code == 404
    granted = client.post(
        f"/api/patient-companion/admin/patients/{patient_a.id}/shares",
        headers=headers,
        json={"resource_type": "media", "resource_id": media_a.id},
    )
    assert granted.status_code == 201, granted.text

    client.cookies.clear()
    shares = client.get(
        f"/api/patient-companion/contexts/{access_a}/shares",
        headers={"Authorization": "Bearer firebase-a"},
    )
    assert shares.status_code == 200, shares.text
    assert [item["resource_id"] for item in shares.json()["items"]] == [media_a.id]


def test_staff_revocation_removes_patient_context(client, db):
    owner = _user(db, email="owner-revoke@test.local")
    patient = _patient(db, owner, nom="Revoke")
    headers = _login(client, owner)
    invite = _create_invitation(client, headers, patient.id)
    activation = _activate(client, "firebase-a", token=invite["qr_token"])
    assert activation.status_code == 200
    access_id = activation.json()["access_id"]
    revoked = client.post(
        f"/api/patient-companion/admin/accesses/{access_id}/revoke",
        headers=headers,
    )
    assert revoked.status_code == 200, revoked.text

    client.cookies.clear()
    me = client.get("/api/patient-companion/me", headers={"Authorization": "Bearer firebase-a"})
    assert me.status_code == 403


def test_staff_jwt_is_not_accepted_as_patient_credential(client, db):
    owner = _user(db, email="owner-separation@test.local")
    headers = _login(client, owner)
    client.cookies.clear()
    response = client.get("/api/patient-companion/me", headers=headers)
    assert response.status_code == 401


def test_firebase_verifier_requests_revocation_check(monkeypatch):
    from backend.services import firebase_patient_auth as service

    sentinel_app = object()
    seen = {}
    monkeypatch.setattr(service, "_ensure_firebase_app", lambda: sentinel_app)

    def _verify(token, *, app, check_revoked):
        seen.update(token=token, app=app, check_revoked=check_revoked)
        return {
            "uid": "firebase-subject-test",
            "iat": 1_700_000_000,
            "exp": 1_700_003_600,
            "auth_time": 1_700_000_000,
        }

    monkeypatch.setattr(service.firebase_auth, "verify_id_token", _verify)
    credential = service.verify_patient_id_token("opaque-firebase-token")
    assert credential.subject == "firebase-subject-test"
    assert seen == {
        "token": "opaque-firebase-token",
        "app": sentinel_app,
        "check_revoked": True,
    }
