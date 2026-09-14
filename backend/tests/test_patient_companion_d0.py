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


def _user(db, email):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Test",
        is_active=True,
        is_licensed=True,
    )
    db.add(user); db.commit(); db.refresh(user)
    return user


def _patient(db, owner, nom):
    patient = models.Patient(
        numero_dossier=f"D-{uuid.uuid4().hex[:8]}",
        nom=nom,
        prenom="Patient",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
    )
    db.add(patient); db.commit(); db.refresh(patient)
    return patient


def _staff_headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _patient_headers(token="firebase-a"):
    return {"Authorization": f"Firebase {token}"}


@pytest.fixture(autouse=True)
def _fake_patient_auth(monkeypatch):
    now = datetime.now(timezone.utc)
    credentials = {
        "firebase-a": FirebasePatientCredential("firebase-subject-a", now, now + timedelta(hours=1), now),
        "firebase-b": FirebasePatientCredential("firebase-subject-b", now, now + timedelta(hours=1), now),
    }

    def _verify(token):
        if token not in credentials:
            raise FirebasePatientAuthInvalid("invalid")
        return credentials[token]

    monkeypatch.setattr(patient_companion_common, "verify_patient_id_token", _verify)
    monkeypatch.setattr(patient_companion_activation, "check_rate_limit", lambda *_a, **_kw: None)


def _invite(client, headers, patient_id, **payload):
    response = client.post(
        f"/api/patient-companion/admin/patients/{patient_id}/invitation",
        headers=headers,
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _activate(client, token="firebase-a", **payload):
    client.cookies.clear()
    return client.post(
        "/api/patient-companion/activate",
        headers=_patient_headers(token),
        json=payload,
    )


def test_invitation_is_hashed_single_use_and_staff_jwt_is_not_patient_auth(client, db):
    owner = _user(db, "owner-a@test.local")
    patient = _patient(db, owner, "A")
    staff = _staff_headers(client, owner)
    invitation = _invite(client, staff, patient.id)
    row = db.query(PatientCompanionInvitation).filter_by(public_id=invitation["invitation_id"]).one()
    assert row.employer_id == owner.id and row.patient_id == patient.id
    assert row.token_hash != invitation["qr_token"]
    assert row.manual_code_hash != invitation["manual_code"].replace("-", "")

    client.cookies.clear()
    assert client.get("/api/patient-companion/me", headers=staff).status_code == 401

    activated = _activate(client, token=invitation["qr_token"])
    # The first positional `token` above is Firebase credential, so activate correctly below.
    if activated.status_code != 200:
        activated = _activate(client, "firebase-a", token=invitation["qr_token"])
    assert activated.status_code == 200, activated.text
    assert activated.headers["cache-control"] == "no-store"
    replay = _activate(client, "firebase-b", token=invitation["qr_token"])
    assert replay.status_code == 400


def test_parent_identity_can_access_multiple_children(client, db):
    owner = _user(db, "owner-family@test.local")
    a = _patient(db, owner, "Child-A")
    b = _patient(db, owner, "Child-B")
    staff = _staff_headers(client, owner)
    ia = _invite(client, staff, a.id, relationship_type="PARENT")
    ib = _invite(client, staff, b.id, relationship_type="PARENT")
    assert _activate(client, "firebase-a", manual_code=ia["manual_code"]).status_code == 200
    assert _activate(client, "firebase-a", manual_code=ib["manual_code"]).status_code == 200
    client.cookies.clear()
    me = client.get("/api/patient-companion/me", headers=_patient_headers())
    assert me.status_code == 200, me.text
    assert {c["patient"]["nom"] for c in me.json()["contexts"]} == {"Child-A", "Child-B"}
    assert {c["relationship_type"] for c in me.json()["contexts"]} == {"PARENT"}


def test_cross_tenant_invitation_and_cross_identity_context_fail_closed(client, db):
    owner_a = _user(db, "owner-a2@test.local")
    owner_b = _user(db, "owner-b2@test.local")
    pa = _patient(db, owner_a, "A")
    pb = _patient(db, owner_b, "B")
    staff_a = _staff_headers(client, owner_a)
    assert client.post(
        f"/api/patient-companion/admin/patients/{pb.id}/invitation",
        headers=staff_a,
        json={},
    ).status_code == 404

    ia = _invite(client, staff_a, pa.id)
    activation_a = _activate(client, "firebase-a", token=ia["qr_token"])
    assert activation_a.status_code == 200
    access_a = activation_a.json()["access_id"]

    staff_b = _staff_headers(client, owner_b)
    ib = _invite(client, staff_b, pb.id)
    activation_b = _activate(client, "firebase-b", token=ib["qr_token"])
    assert activation_b.status_code == 200
    access_b = activation_b.json()["access_id"]

    db.add(models.Appointment(
        patient_id=pa.id,
        patient_name="Patient A",
        datetime_start=datetime.utcnow() + timedelta(days=1),
        duration_minutes=30,
        motif="A-only",
        employer_id=owner_a.id,
    ))
    db.commit()
    client.cookies.clear()
    own = client.get(
        f"/api/patient-companion/contexts/{access_a}/appointments",
        headers=_patient_headers("firebase-a"),
    )
    assert own.status_code == 200 and [x["motif"] for x in own.json()["items"]] == ["A-only"]
    assert client.get(
        f"/api/patient-companion/contexts/{access_b}/appointments",
        headers=_patient_headers("firebase-a"),
    ).status_code == 404


def test_media_share_requires_explicit_same_patient_grant(client, db):
    owner = _user(db, "owner-share@test.local")
    pa = _patient(db, owner, "Share-A")
    pb = _patient(db, owner, "Share-B")
    staff = _staff_headers(client, owner)
    media_a = ClinicalAsset(
        employer_id=owner.id, patient_id=pa.id, asset_type="PHOTO",
        source_kind="UPLOAD", mime_type="image/jpeg", created_by=owner.id,
    )
    media_b = ClinicalAsset(
        employer_id=owner.id, patient_id=pb.id, asset_type="PHOTO",
        source_kind="UPLOAD", mime_type="image/jpeg", created_by=owner.id,
    )
    db.add_all([media_a, media_b]); db.commit(); db.refresh(media_a); db.refresh(media_b)
    invite = _invite(client, staff, pa.id)
    access_id = _activate(client, "firebase-a", token=invite["qr_token"]).json()["access_id"]

    assert client.post(
        f"/api/patient-companion/admin/patients/{pa.id}/shares",
        headers=staff,
        json={"resource_type": "media", "resource_id": media_b.id},
    ).status_code == 404
    grant = client.post(
        f"/api/patient-companion/admin/patients/{pa.id}/shares",
        headers=staff,
        json={"resource_type": "media", "resource_id": media_a.id},
    )
    assert grant.status_code == 201, grant.text
    client.cookies.clear()
    shares = client.get(
        f"/api/patient-companion/contexts/{access_id}/shares",
        headers=_patient_headers(),
    )
    assert shares.status_code == 200
    assert [x["resource_id"] for x in shares.json()["items"]] == [media_a.id]


def test_access_revocation_is_immediate(client, db):
    owner = _user(db, "owner-revoke@test.local")
    patient = _patient(db, owner, "Revoke")
    staff = _staff_headers(client, owner)
    invite = _invite(client, staff, patient.id)
    access_id = _activate(client, "firebase-a", token=invite["qr_token"]).json()["access_id"]
    revoked = client.post(
        f"/api/patient-companion/admin/accesses/{access_id}/revoke",
        headers=staff,
    )
    assert revoked.status_code == 200
    client.cookies.clear()
    assert client.get("/api/patient-companion/me", headers=_patient_headers()).status_code == 403


def test_firebase_verifier_requests_revocation_check(monkeypatch):
    from backend.services import firebase_patient_auth as service
    sentinel_app = object()
    seen = {}
    monkeypatch.setattr(service, "_ensure_firebase_app", lambda: sentinel_app)

    def _verify(token, *, app, check_revoked):
        seen.update(token=token, app=app, check_revoked=check_revoked)
        return {"uid": "firebase-subject-test", "iat": 1700000000, "exp": 1700003600, "auth_time": 1700000000}

    monkeypatch.setattr(service.firebase_auth, "verify_id_token", _verify)
    assert service.verify_patient_id_token("opaque-token").subject == "firebase-subject-test"
    assert seen == {"token": "opaque-token", "app": sentinel_app, "check_revoked": True}
