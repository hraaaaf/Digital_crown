"""PC-00 local-first Patient Companion security contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_patient_companion_router_is_mounted_and_pairing_body_is_bounded():
    main = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'app.include_router(patient_companion.router, prefix="/api/patient-companion"' in main
    assert '"/api/patient-companion/pair",' in main
    assert 'token_type == "patient_companion"' in main


def test_local_pairing_is_one_time_and_does_not_require_firebase():
    source = (ROOT / "routers" / "patient_companion_pairing.py").read_text(encoding="utf-8")
    assert '@router.post("/pair", status_code=201)' in source
    assert 'recipient_type == "local_bridge"' in source
    assert 'PatientCompanionInvitation.consumed_at.is_(None)' in source
    assert 'PatientCompanionInvitation.consumed_at: now' in source
    assert '"storage_policy": "local_encrypted_device"' in source
    assert "FirebasePatientCredential" not in source
    assert "verify_patient_id_token" not in source


def test_patient_device_token_is_scoped_to_active_access_and_tenant():
    source = (ROOT / "routers" / "patient_companion_common.py").read_text(encoding="utf-8")
    assert '"type": "patient_companion"' in source
    assert '"access_id": access.public_id' in source
    assert '"tenant_id": access.employer_id' in source
    assert 'PatientCompanionAccess.revoked_at.is_(None)' in source
    assert 'PatientCompanionIdentity.provider == LOCAL_BRIDGE_PROVIDER' in source


def test_patient_wallet_does_not_expose_internal_numeric_ids():
    activation = (ROOT / "routers" / "patient_companion_activation.py").read_text(encoding="utf-8")
    shares = (ROOT / "routers" / "patient_companion_shares.py").read_text(encoding="utf-8")
    assert '"id": row.id' not in activation
    assert '"resource_id": resource.id' not in shares
    assert '"resource_id": resource.id' not in shares
