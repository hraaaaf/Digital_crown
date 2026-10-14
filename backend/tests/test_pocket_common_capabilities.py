from datetime import datetime
from types import SimpleNamespace
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import database, models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.routers import mobile_patient_cockpit, patient_companion_activation
from backend.routers.patient_companion_common import create_patient_device_token
from backend.services.pocket_capabilities import patient_read_capabilities, staff_read_capabilities
from backend.services.zka_crypto import decrypt_payload


def _staff(role, permissions, employer_id=1):
    return SimpleNamespace(role=role, permissions=permissions, employer_id=employer_id, email="profile@example.test")


@pytest.mark.parametrize("role,permissions,expected", [
    ("SECRETAIRE", {}, {"agenda.read", "cabinet.patients.read"}),
    ("DENTISTE", {"patients": True, "clinical": True}, {"cabinet.patients.read", "cabinet.clinical.read"}),
    ("DENTISTE", {"agenda": False, "patients": False}, set()),
    ("SECRETAIRE", {"payments": True}, {"cabinet.finance.read"}),
    ("UNKNOWN", {}, set()),
])
def test_effective_settings_permissions_drive_read_capabilities(role, permissions, expected):
    contract = staff_read_capabilities(_staff(role, permissions))
    assert contract["version"] == 1
    assert contract["principal_kind"] == "staff"
    assert {key for key, value in contract["capabilities"].items() if value["allowed"]} == expected
    for key, value in contract["capabilities"].items():
        assert value["scope"] == ("cabinet" if key in expected else None)


@pytest.mark.parametrize("role,employer", [("ADMIN", 1), ("DENTISTE", None)])
def test_existing_owner_admin_policy_is_preserved(role, employer):
    caps = staff_read_capabilities(_staff(role, {"patients": False}, employer))["capabilities"]
    assert caps["cabinet.patients.read"]["allowed"]
    assert caps["cabinet.finance.read"]["allowed"]
    assert not caps["shares.read"]["allowed"]


def test_removed_permissions_and_missing_patient_permission_do_not_grant_clinical_access():
    user = _staff("DENTISTE", {"patients": True, "clinical": True})
    assert staff_read_capabilities(user)["capabilities"]["cabinet.clinical.read"]["allowed"]
    user.permissions = {"clinical": True}
    assert not staff_read_capabilities(user)["capabilities"]["cabinet.clinical.read"]["allowed"]
    user.permissions = {"patients": False, "clinical": False}
    assert not staff_read_capabilities(user)["capabilities"]["cabinet.patients.read"]["allowed"]


def test_patient_uses_same_shape_without_staff_grants_or_internal_identifiers():
    patient = patient_read_capabilities()
    staff = staff_read_capabilities(_staff("ADMIN", {}))
    assert patient["capabilities"].keys() == staff["capabilities"].keys()
    assert patient["principal_kind"] == "patient"
    assert {key for key, value in patient["capabilities"].items() if value["allowed"]} == {"agenda.read", "shares.read"}
    assert all(value["scope"] == "patient_context" for value in patient["capabilities"].values() if value["allowed"])
    assert not {"patient_id", "user_id", "tenant_id", "access_token"} & patient.keys()


def test_staff_endpoint_requires_mobile_auth_and_preserves_encryption():
    from backend.routers import mobile_legacy

    app = FastAPI()
    app.include_router(mobile_patient_cockpit.router, prefix="/api/mobile")
    with TestClient(app) as client:
        assert client.get("/api/mobile/capabilities", headers={"Authorization": "Bearer invalid"}).status_code == 401
        app.dependency_overrides[mobile_legacy.get_mobile_user] = lambda: _staff("SECRETAIRE", {"agenda": True})
        response = client.get("/api/mobile/capabilities")
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert set(response.json()) == {"payload"}
        caps = decrypt_payload(response.json()["payload"])["capabilities"]
        assert caps["agenda.read"]["allowed"]
        assert not caps["cabinet.patients.read"]["allowed"]


def test_patient_context_guard_rejects_other_identity_and_revoked_access(db, dentiste):
    identity = PatientCompanionIdentity(provider="local_bridge", subject="caps-patient")
    other = PatientCompanionIdentity(provider="local_bridge", subject="caps-other")
    patient = models.Patient(numero_dossier="CAPS-TEST", nom="Test", prenom="Patient",
                             date_naissance=datetime(2000, 1, 1), sexe="F", employer_id=dentiste.id)
    db.add_all([identity, other, patient])
    db.flush()
    access = PatientCompanionAccess(identity_id=identity.id, employer_id=dentiste.id, patient_id=patient.id, relationship_type="SELF")
    other_access = PatientCompanionAccess(identity_id=other.id, employer_id=dentiste.id, patient_id=patient.id, relationship_type="CAREGIVER")
    db.add_all([access, other_access])
    db.commit()

    app = FastAPI()
    app.include_router(patient_companion_activation.router, prefix="/api/patient-companion")
    app.include_router(mobile_patient_cockpit.router, prefix="/api/mobile")
    app.dependency_overrides[database.get_db] = lambda: db
    headers = {"Authorization": f"Bearer {create_patient_device_token(identity, access)}"}
    other_headers = {"Authorization": f"Bearer {create_patient_device_token(other, other_access)}"}
    with TestClient(app) as client:
        path = f"/api/patient-companion/contexts/{access.public_id}/capabilities"
        assert client.get(path).status_code == 401
        response = client.get(path, headers=headers)
        assert response.status_code == 200
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["principal_kind"] == "patient"
        assert client.get("/api/mobile/capabilities", headers=headers).status_code == 401
        assert client.get(path, headers=other_headers).status_code == 404
        access.revoked_at = datetime.utcnow()
        db.commit()
        assert client.get(path, headers=headers).status_code == 401


def test_staff_endpoint_reloads_permissions_and_rejects_revoked_device(db, dentiste):
    from backend.routers.mobile import _create_mobile_jwt

    user = models.User(email="capabilities-staff@example.test", hashed_password="test-only",
                       role=models.UserRole.SECRETAIRE, employer_id=dentiste.id,
                       is_active=True, approval_status="approved", permissions={"agenda": True})
    db.add(user)
    db.flush()
    device = models.MobilePairedDevice(device_id=str(uuid.uuid4()), user_id=user.id,
                                      employer_id=dentiste.id, client_public_key_hex="04" + "11" * 64,
                                      refresh_jti="capabilities-test")
    db.add(device)
    db.commit()
    headers = {"Authorization": f"Bearer {_create_mobile_jwt(user.id, 'DENTISTE', dentiste.id, device.device_id)}"}
    app = FastAPI()
    app.include_router(mobile_patient_cockpit.router, prefix="/api/mobile")
    app.include_router(patient_companion_activation.router, prefix="/api/patient-companion")
    app.dependency_overrides[database.get_db] = lambda: db
    with TestClient(app) as client:
        response = client.get("/api/mobile/capabilities", headers=headers)
        assert response.status_code == 200
        assert decrypt_payload(response.json()["payload"])["capabilities"]["agenda.read"]["allowed"]
        assert client.get("/api/patient-companion/contexts/not-owned/capabilities", headers=headers).status_code == 401
        user.permissions = {"agenda": False}
        db.commit()
        response = client.get("/api/mobile/capabilities", headers=headers)
        assert response.status_code == 200
        assert not decrypt_payload(response.json()["payload"])["capabilities"]["agenda.read"]["allowed"]
        device.revoked_at = datetime.utcnow()
        db.commit()
        assert client.get("/api/mobile/capabilities", headers=headers).status_code == 401
