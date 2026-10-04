from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

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


def test_station_patient_session_db_enforces_single_active_session(client, db, dentiste):
    headers, workstation_id = _station(client, dentiste)
    created = client.post("/api/workstation/patient-session", headers=headers)
    assert created.status_code == 201, created.text

    duplicate = models.WorkstationPatientSession(
        employer_id=dentiste.id,
        workstation_id=workstation_id,
        claim_token_hash="f" * 64,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(seconds=120),
    )
    db.add(duplicate)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


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


def _cabinet_config(db, owner):
    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == owner.id).first()
    if config is None:
        config = models.CabinetConfig(
            owner_id=owner.id,
            nom_cabinet="Cabinet Test",
            nom_praticien=owner.nom_complet or "Dr Test",
            is_initialized=True,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def test_fallback_phone_and_birth_date_identifies_without_exposing_arrival(client, db, dentiste):
    config = _cabinet_config(db, dentiste)
    config.station_identification_fallback = "phone_dob"
    db.commit()
    headers, _ = _station(client, dentiste)
    patient = models.Patient(
        numero_dossier="ST03-FB-PHONE",
        nom="Fallback",
        prenom="Aya",
        date_naissance=datetime(1992, 5, 4),
        sexe="F",
        employer_id=dentiste.id,
        telephone="+212612345678",
    )
    db.add(patient)
    db.commit()

    created_response = client.post("/api/workstation/patient-session", headers=headers)
    assert created_response.status_code == 201, created_response.text
    created = created_response.json()
    assert created["fallbackMode"] == "phone_dob"

    identified = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/fallback",
        headers=headers,
        json={"birthDate": "1992-05-04", "phone": "+212 612-345-678"},
    )
    assert identified.status_code == 200, identified.text
    assert identified.json()["status"] == "identified"
    assert identified.json()["displayName"] == "Aya Fallback"
    assert "arriv" not in identified.text.lower()

    replay = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/fallback",
        headers=headers,
        json={"birthDate": "1992-05-04", "phone": "+212612345678"},
    )
    assert replay.status_code == 409

    audit = db.query(models.AuditLog).filter(
        models.AuditLog.employer_id == dentiste.id,
        models.AuditLog.action == "STATION_PATIENT_FALLBACK_IDENTIFIED",
    ).one()
    assert "credentials not logged" in audit.details


def test_fallback_collision_fails_generically_and_locks_after_five_attempts(client, db, dentiste):
    config = _cabinet_config(db, dentiste)
    config.station_identification_fallback = "phone_dob"
    db.commit()
    headers, _ = _station(client, dentiste)
    for dossier, name in (("ST03-COLLIDE-1", "Aya"), ("ST03-COLLIDE-2", "Nora")):
        db.add(models.Patient(
            numero_dossier=dossier,
            nom="Collision",
            prenom=name,
            date_naissance=datetime(1990, 6, 7),
            sexe="F",
            employer_id=dentiste.id,
            telephone="0612345678",
        ))
    db.commit()

    created = client.post("/api/workstation/patient-session", headers=headers).json()
    url = f"/api/workstation/patient-session/{created['sessionId']}/fallback"

    for attempt in range(1, 6):
        response = client.post(
            url,
            headers=headers,
            json={"birthDate": "1990-06-07", "phone": "0612345678"},
        )
        assert response.status_code == (429 if attempt == 5 else 403)
        if attempt < 5:
            assert response.json()["detail"] == "IDENTIFICATION_NOT_CONFIRMED"

    db.expire_all()
    row = db.query(models.WorkstationPatientSession).filter(
        models.WorkstationPatientSession.id == created["sessionId"]
    ).one()
    assert row.fallback_failed_attempts == 5
    assert row.patient_id is None
    assert row.claimed_at is None


def test_fallback_lock_survives_session_regeneration(client, db, dentiste):
    config = _cabinet_config(db, dentiste)
    config.station_identification_fallback = "phone_dob"
    db.commit()
    headers, _ = _station(client, dentiste)
    patient = models.Patient(
        numero_dossier="ST03-REGEN-LOCK",
        nom="Target",
        prenom="Nora",
        date_naissance=datetime(1991, 7, 8),
        sexe="F",
        employer_id=dentiste.id,
        telephone="0611223344",
    )
    db.add(patient)
    db.commit()

    for attempt in range(1, 6):
        created = client.post("/api/workstation/patient-session", headers=headers)
        assert created.status_code == 201, created.text
        response = client.post(
            f"/api/workstation/patient-session/{created.json()['sessionId']}/fallback",
            headers=headers,
            json={"birthDate": "1991-07-08", "phone": "0699999999"},
        )
        assert response.status_code == (429 if attempt == 5 else 403), response.text

    regenerated = client.post("/api/workstation/patient-session", headers=headers)
    assert regenerated.status_code == 201, regenerated.text
    locked = client.post(
        f"/api/workstation/patient-session/{regenerated.json()['sessionId']}/fallback",
        headers=headers,
        json={"birthDate": "1991-07-08", "phone": "0611223344"},
    )
    assert locked.status_code == 429
    assert locked.json()["detail"] == "STATION_FALLBACK_LOCKED"


def test_fallback_mode_is_owner_pin_configurable_and_name_mode_normalizes_text(client, db, dentiste):
    config = _cabinet_config(db, dentiste)
    config.station_identification_fallback = "phone_dob"
    db.commit()

    headers, _ = _station(client, dentiste)
    current = client.get("/api/workstation/patient-session/config", headers=headers)
    assert current.status_code == 200
    assert current.json()["fallbackMode"] == "phone_dob"

    wrong = client.patch(
        "/api/workstation/patient-session/config",
        headers=headers,
        json={"fallbackMode": "name_dob", "ownerPin": "0000"},
    )
    assert wrong.status_code == 403

    changed = client.patch(
        "/api/workstation/patient-session/config",
        headers=headers,
        json={"fallbackMode": "name_dob", "ownerPin": "2468"},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["fallbackMode"] == "name_dob"

    patient = models.Patient(
        numero_dossier="ST03-FB-NAME",
        nom="Benmoussa",
        prenom="Élodie",
        date_naissance=datetime(1988, 2, 3),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()

    created = client.post("/api/workstation/patient-session", headers=headers).json()
    assert created["fallbackMode"] == "name_dob"
    identified = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/fallback",
        headers=headers,
        json={"birthDate": "1988-02-03", "firstName": "elodie", "lastName": " BENMOUSSA "},
    )
    assert identified.status_code == 200, identified.text
    assert identified.json()["displayName"] == "Élodie Benmoussa"


def test_fallback_invalid_config_fails_closed(client, db, dentiste):
    config = _cabinet_config(db, dentiste)
    config.station_identification_fallback = "unexpected"
    db.commit()
    headers, _ = _station(client, dentiste)

    created = client.post("/api/workstation/patient-session", headers=headers)
    assert created.status_code == 201, created.text
    assert created.json()["fallbackMode"] == "disabled"

    denied = client.post(
        f"/api/workstation/patient-session/{created.json()['sessionId']}/fallback",
        headers=headers,
        json={"birthDate": "1992-05-04", "phone": "0612345678"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "STATION_FALLBACK_DISABLED"


def test_fallback_can_be_disabled_by_cabinet(client, db, dentiste):
    config = _cabinet_config(db, dentiste)
    config.station_identification_fallback = "phone_dob"
    db.commit()
    headers, _ = _station(client, dentiste)

    changed = client.patch(
        "/api/workstation/patient-session/config",
        headers=headers,
        json={"fallbackMode": "disabled", "ownerPin": "2468"},
    )
    assert changed.status_code == 200

    created = client.post("/api/workstation/patient-session", headers=headers).json()
    assert created["fallbackMode"] == "disabled"
    denied = client.post(
        f"/api/workstation/patient-session/{created['sessionId']}/fallback",
        headers=headers,
        json={"birthDate": "1992-05-04", "phone": "0612345678"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "STATION_FALLBACK_DISABLED"
