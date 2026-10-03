from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers.patient_companion_common import create_patient_device_token
from backend.security import get_password_hash


def _login(client, email: str, password: str = "TestPass123!") -> dict[str, str]:
    response = client.post("/api/auth/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    client.cookies.delete("access_token")
    client.cookies.delete("refresh_token")
    return {"Authorization": f"Bearer {token}"}


def _station(client, owner) -> tuple[dict[str, str], str]:
    headers = _login(client, owner.email)
    state = client.get("/api/workstation/state", headers=headers)
    assert state.status_code == 200, state.text
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
    return headers, mode.json()["workstationId"]


def _patient_context(db, owner, *, dossier="ST03-001", name="Aya"):
    patient = models.Patient(
        numero_dossier=dossier,
        nom="Audit",
        prenom=name,
        date_naissance=datetime(2010, 1, 1),
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
    return patient, access, {"Authorization": f"Bearer {create_patient_device_token(identity, access)}"}


def test_station_patient_session_is_station_bound_opaque_and_short_lived(client, db, dentiste):
    headers, workstation_id = _station(client, dentiste)

    created = client.post("/api/workstation/patient-session", headers=headers)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["sessionId"]
    assert body["handoffUrl"] == body["nfcPayload"]
    assert "stationSession=" in body["handoffUrl"]
    assert body["qrDataUrl"].startswith("data:image/png;base64,")
    assert dentiste.email not in body["handoffUrl"]

    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == body["sessionId"]
    ).one()
    assert row.workstation_id == workstation_id
    assert row.patient_id is None
    assert row.patient_access_id is None
    assert row.claim_token_hash not in body["handoffUrl"]
    assert 0 < (row.expires_at - row.created_at).total_seconds() <= 120

    status = client.get(f"/api/workstation/patient-session/{row.id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["status"] == "pending"


def test_patient_companion_claim_is_atomic_one_shot_and_purgeable(client, db, dentiste):
    headers, _ = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=headers).json()
    raw = created["handoffUrl"].split("stationSession=", 1)[1]

    patient, access, patient_headers = _patient_context(db, dentiste)

    claimed = client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": raw, "accessId": access.public_id},
    )
    assert claimed.status_code == 200, claimed.text
    assert claimed.json()["status"] == "identified"

    replay = client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": raw, "accessId": access.public_id},
    )
    assert replay.status_code == 409

    station_view = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}",
        headers=headers,
    )
    assert station_view.status_code == 200
    assert station_view.json()["status"] == "identified"
    assert station_view.json()["displayName"] == "Aya Audit"

    purged = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/purge",
        headers=headers,
    )
    assert purged.status_code == 204
    db.expire_all()
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == created["sessionId"]
    ).one()
    assert row.purged_at is not None
    assert row.patient_id is None
    assert row.patient_access_id is None

    expired_view = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}",
        headers=headers,
    )
    assert expired_view.status_code == 200
    assert expired_view.json()["status"] == "expired"


def test_station_patient_claim_hides_cross_tenant_session(client, db, dentiste):
    headers, _ = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=headers).json()
    raw = created["handoffUrl"].split("stationSession=", 1)[1]

    other = models.User(
        email="station.other.owner@cabinet.ma",
        hashed_password=get_password_hash("OtherPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet="Other Owner",
        is_active=True,
        is_licensed=True,
        employer_id=None,
    )
    db.add(other)
    db.commit()
    _, access, other_headers = _patient_context(db, other, dossier="ST03-OTHER", name="Nora")

    denied = client.post(
        "/api/workstation/patient-session/claim",
        headers=other_headers,
        json={"token": raw, "accessId": access.public_id},
    )
    assert denied.status_code == 404

    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == created["sessionId"]
    ).one()
    assert row.claimed_at is None
    assert row.patient_id is None


def test_expired_station_session_purges_patient_references(client, db, dentiste):
    headers, _ = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=headers).json()
    raw = created["handoffUrl"].split("stationSession=", 1)[1]
    patient, access, patient_headers = _patient_context(db, dentiste, dossier="ST03-EXP")

    assert client.post(
        "/api/workstation/patient-session/claim",
        headers=patient_headers,
        json={"token": raw, "accessId": access.public_id},
    ).status_code == 200

    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == created["sessionId"]
    ).one()
    row.expires_at = datetime.utcnow() - timedelta(seconds=1)
    db.commit()

    expired = client.get(
        f"/api/workstation/patient-session/{created['sessionId']}",
        headers=headers,
    )
    assert expired.status_code == 200
    assert expired.json()["status"] == "expired"
    db.expire_all()
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == created["sessionId"]
    ).one()
    assert row.purged_at is not None
    assert row.patient_id is None
    assert row.patient_access_id is None
