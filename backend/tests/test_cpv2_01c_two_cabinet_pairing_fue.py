"""CPV2-01C FUE-I lab: real FastAPI pairing for two disposable tenant identities.

No backend mocking, no real patient data, no claims of physical PWA pairing.
The HTTP API is real; pytest's SQLite in-memory database is synthetic/isolated.
"""
from datetime import datetime, timedelta

from backend import models
from backend.core.key_material import mobile_pairing_key_hex
from backend.routers.mobile import _create_bridge_token
from backend.security import token_blacklist
from backend.tests.test_mobile_pocket_security_boundary import _client_public_key, _user


def _pair(client, db, owner, staff, manual_code: str, public_id: str):
    owner.is_licensed = True
    owner.license_expires_at = datetime.utcnow() + timedelta(days=30)
    db.add(owner)
    db.commit()
    record = models.ZKAPairingToken(
        token=_create_bridge_token("agenda"),
        manual_code=manual_code,
        employer_id=owner.id,
        user_id=staff.id,
        public_id=public_id,
        master_key=mobile_pairing_key_hex(),
        role=staff.role.value if hasattr(staff.role, "value") else str(staff.role),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()
    response = client.post("/api/mobile/claim-token", json={
        "token": record.token,
        "client_public_key_hex": _client_public_key(),
    })
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload.get("access_token") and payload.get("device_id")
    assert payload.get("encrypted_master_key_hex")
    assert "masterKey" not in payload and "master_key" not in payload
    replay = client.post("/api/mobile/claim-token", json={
        "token": record.token,
        "client_public_key_hex": _client_public_key(),
    })
    assert replay.status_code == 404, replay.text
    return payload["access_token"]


def test_two_genuine_paired_tenants_a_b_a_fail_closed(client, db, dentiste):
    # Two independent TEST clinics, using the real mobile pairing endpoint.
    owner_a = dentiste
    owner_b = _user(
        db, email="cpv2-test-owner-b@cabinet.invalid",
        role=models.UserRole.DENTISTE, permissions={"agenda": True, "patients": True},
    )
    staff_a = _user(
        db, email="cpv2-test-staff-a@cabinet.invalid",
        role=models.UserRole.SECRETAIRE, employer_id=owner_a.id,
        permissions={"agenda": True, "patients": True, "clinical": False},
    )
    staff_b = _user(
        db, email="cpv2-test-staff-b@cabinet.invalid",
        role=models.UserRole.SECRETAIRE, employer_id=owner_b.id,
        permissions={"agenda": True, "patients": True, "clinical": False},
    )

    patient_a = models.Patient(
        nom="CANARY-A", prenom="TEST", sexe="F",
        date_naissance=datetime(1990, 1, 2), employer_id=owner_a.id,
    )
    patient_b = models.Patient(
        nom="CANARY-B", prenom="TEST", sexe="M",
        date_naissance=datetime(1991, 2, 3), employer_id=owner_b.id,
    )
    db.add_all([patient_a, patient_b])
    db.commit()
    db.refresh(patient_a)
    db.refresh(patient_b)

    token_a = _pair(client, db, owner_a, staff_a, "714231", "aaaaaaaaaaaaaaaa")
    token_b = _pair(client, db, owner_b, staff_b, "714232", "bbbbbbbbbbbbbbbb")
    a = {"Authorization": f"Bearer {token_a}"}
    b = {"Authorization": f"Bearer {token_b}"}

    # Genuine HTTP + token-based tenant verification in A -> B -> A order.
    own_a = client.get(f"/api/mobile/patient-cockpit/{patient_a.id}", headers=a)
    assert own_a.status_code == 200, own_a.text
    cross_b_a = client.get(f"/api/mobile/patient-cockpit/{patient_a.id}", headers=b)
    assert cross_b_a.status_code in (403, 404), cross_b_a.text

    own_b = client.get(f"/api/mobile/patient-cockpit/{patient_b.id}", headers=b)
    assert own_b.status_code == 200, own_b.text
    cross_a_b = client.get(f"/api/mobile/patient-cockpit/{patient_b.id}", headers=a)
    assert cross_a_b.status_code in (403, 404), cross_a_b.text

    back_to_a = client.get(f"/api/mobile/patient-cockpit/{patient_a.id}", headers=a)
    assert back_to_a.status_code == 200, back_to_a.text

    # A paired mobile JWT must not be usable as a desktop clinical session.
    assert client.get("/api/patients/", headers=a).status_code == 401
    assert client.get("/api/patients/", headers=b).status_code == 401

    # Revoking A must not revoke B or reveal a cross-tenant patient.
    token_blacklist.revoke(token_a, db)
    assert client.get(f"/api/mobile/patient-cockpit/{patient_a.id}", headers=a).status_code == 401
    assert client.get(f"/api/mobile/patient-cockpit/{patient_b.id}", headers=b).status_code == 200
    assert client.get(f"/api/mobile/patient-cockpit/{patient_a.id}", headers=b).status_code in (403, 404)
