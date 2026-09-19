from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionInvitation
from backend.routers.patient_companion_common import manual_code_hash, token_hash


def _patient(db, owner):
    patient = models.Patient(
        numero_dossier="PC00-001",
        nom="Audit",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=owner.id,
        email="aya@example.test",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_local_pairing_is_runtime_reachable_offline_first_and_revocable(client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)
    patient = _patient(db, dentiste)
    raw_token = "pc00-runtime-one-shot-token"
    manual_code = "ABCD-EFGH-JKLM"
    invitation = PatientCompanionInvitation(
        employer_id=dentiste.id,
        patient_id=patient.id,
        token_hash=token_hash(raw_token),
        manual_code_hash=manual_code_hash(manual_code),
        recipient_type="local_bridge",
        recipient_hash=token_hash("runtime-placeholder"),
        relationship_type="SELF",
        created_by_user_id=dentiste.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(invitation)
    db.commit()

    paired = client.post("/api/patient-companion/pair", json={"token": raw_token})
    assert paired.status_code == 201, paired.text
    payload = paired.json()
    assert payload["storage_policy"] == "local_encrypted_device"
    assert payload["context"]["patient"]["display_name"] == "Aya Audit"
    assert payload["context"]["relationship_type"] == "SELF"
    assert "patient_id" not in payload["context"]
    assert payload["access_token"]

    # The one-shot invitation cannot be replayed.
    replay = client.post("/api/patient-companion/pair", json={"token": raw_token})
    assert replay.status_code == 400

    headers = {"Authorization": f"Bearer {payload['access_token']}"}
    me = client.get("/api/patient-companion/me", headers=headers)
    assert me.status_code == 200, me.text
    assert me.json()["contexts"][0]["access_id"] == payload["context"]["access_id"]

    # Revocation cuts future synchronization even if the phone keeps its local copy.
    access = db.query(PatientCompanionAccess).filter(
        PatientCompanionAccess.public_id == payload["context"]["access_id"]
    ).one()
    access.revoked_at = datetime.utcnow()
    db.commit()

    revoked = client.get("/api/patient-companion/me", headers=headers)
    assert revoked.status_code == 401
