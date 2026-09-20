from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionInvitation,
    PatientCompanionRelayBinding,
    PatientCompanionRemoteKeyset,
)
from backend.routers.patient_companion_common import manual_code_hash, token_hash
from backend.services.patient_companion_key_protection import OsKeyProtectionUnavailable
from backend.services.patient_companion_remote_crypto import generate_p256_keypair
from backend.services.patient_companion_remote_keys import enroll_remote_keyset as real_enroll


@pytest.fixture()
def focused_client(db):
    """Focused Patient Companion app: real routers/dependencies, no global backend.main bootstrap."""
    from backend.routers import auth as auth_router
    from backend.routers import (
        patient_companion_agenda,
        patient_companion_common,
        patient_companion_pairing,
        patient_companion_shares,
    )

    app = FastAPI()

    def _override_get_db():
        yield db

    app.dependency_overrides[patient_companion_common.get_db] = _override_get_db
    app.dependency_overrides[auth_router.get_db] = _override_get_db
    app.include_router(patient_companion_pairing.router, prefix="/api/patient-companion")
    app.include_router(patient_companion_agenda.router, prefix="/api/patient-companion")
    app.include_router(patient_companion_shares.router, prefix="/api/patient-companion")

    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client



def _invitation(db, owner, suffix: str):
    patient = models.Patient(
        numero_dossier=f"PCRPAIR-{suffix}",
        nom="Remote",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=owner.id,
    )
    db.add(patient)
    db.flush()
    raw = f"remote-pair-token-{suffix}"
    invitation = PatientCompanionInvitation(
        employer_id=owner.id,
        patient_id=patient.id,
        token_hash=token_hash(raw),
        manual_code_hash=manual_code_hash(f"ABCD-{suffix[:4]}-WXYZ"),
        recipient_type="local_bridge",
        recipient_hash=token_hash(f"placeholder-{suffix}"),
        relationship_type="SELF",
        created_by_user_id=owner.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return raw, invitation


def _remote_keys():
    sig_kid = str(uuid.uuid4())
    enc_kid = str(uuid.uuid4())
    _sig_secret, sig_public = generate_p256_keypair(kid=sig_kid, use="sig")
    _enc_secret, enc_public = generate_p256_keypair(kid=enc_kid, use="enc")
    return {
        "signing_kid": sig_kid,
        "signing_public_jwk": sig_public,
        "encryption_kid": enc_kid,
        "encryption_public_jwk": enc_public,
    }


def test_qr_pairing_atomically_enrolls_remote_public_keys(focused_client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)

    def enroll_with_test_protector(*args, **kwargs):
        return real_enroll(
            *args,
            **kwargs,
            protect=lambda clear: b"test-protected:" + clear,
        )

    monkeypatch.setattr(patient_companion_pairing, "enroll_remote_keyset", enroll_with_test_protector)
    raw, invitation = _invitation(db, dentiste, "0001")
    response = focused_client.post(
        "/api/patient-companion/pair",
        json={"token": raw, "remote_keys": _remote_keys()},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["remote_transport"]["status"] == "enrolled"
    assert payload["remote_transport"]["protocol_version"] == "dc-pc-remote-v1"
    assert "private" not in response.text.lower()
    assert db.query(PatientCompanionRemoteKeyset).count() == 1
    assert db.query(PatientCompanionAccess).count() == 1
    db.refresh(invitation)
    assert invitation.consumed_at is not None


def test_qr_pairing_rolls_back_when_os_key_protection_is_unavailable(focused_client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)

    def fail_enrollment(*args, **kwargs):
        raise OsKeyProtectionUnavailable("test unavailable")

    monkeypatch.setattr(patient_companion_pairing, "enroll_remote_keyset", fail_enrollment)
    raw, invitation = _invitation(db, dentiste, "0002")

    response = focused_client.post(
        "/api/patient-companion/pair",
        json={"token": raw, "remote_keys": _remote_keys()},
    )
    assert response.status_code == 503
    assert db.query(PatientCompanionAccess).count() == 0
    assert db.query(PatientCompanionRemoteKeyset).count() == 0
    db.refresh(invitation)
    assert invitation.consumed_at is None


def test_access_revocation_revokes_remote_keyset_in_same_cabinet_flow(
    focused_client, db, dentiste, monkeypatch
):
    from backend.routers import patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)

    def enroll_with_test_protector(*args, **kwargs):
        return real_enroll(
            *args,
            **kwargs,
            protect=lambda clear: b"test-protected:" + clear,
        )

    monkeypatch.setattr(patient_companion_pairing, "enroll_remote_keyset", enroll_with_test_protector)
    raw, _invitation_row = _invitation(db, dentiste, "0003")

    paired = focused_client.post(
        "/api/patient-companion/pair",
        json={"token": raw, "remote_keys": _remote_keys()},
    )
    assert paired.status_code == 201, paired.text
    access_id = paired.json()["context"]["access_id"]
    access = db.query(PatientCompanionAccess).one()
    binding = PatientCompanionRelayBinding(
        access_id=access.id,
        relay_url="https://relay.test",
        cabinet_inbox_id=str(uuid.uuid4()),
        patient_inbox_id=str(uuid.uuid4()),
        protected_cabinet_read_cap_b64="protected-cabinet-read",
        protected_patient_write_cap_b64="protected-patient-write",
        status="ACTIVE",
    )
    db.add(binding)
    db.commit()

    from backend.security import create_access_token

    staff_token = create_access_token({"sub": dentiste.email})
    revoked = focused_client.post(
        f"/api/patient-companion/admin/accesses/{access_id}/revoke",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert revoked.status_code == 200, revoked.text

    keyset = db.query(PatientCompanionRemoteKeyset).one()
    db.refresh(keyset)
    assert keyset.status == "REVOKED"
    assert keyset.revoked_at is not None
    db.refresh(binding)
    assert binding.status == "REVOKE_PENDING"
    assert binding.revoked_at is None


def test_agenda_remote_command_requires_active_keyset_and_dispatches_ciphertext(
    focused_client, db, dentiste, monkeypatch
):
    from backend.routers import patient_companion_agenda, patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)
    monkeypatch.setattr(patient_companion_agenda, "check_rate_limit", lambda *args, **kwargs: None)

    def enroll_with_test_protector(*args, **kwargs):
        return real_enroll(
            *args,
            **kwargs,
            protect=lambda clear: b"test-protected:" + clear,
        )

    monkeypatch.setattr(patient_companion_pairing, "enroll_remote_keyset", enroll_with_test_protector)
    raw, _invitation_row = _invitation(db, dentiste, "0004")
    paired = focused_client.post(
        "/api/patient-companion/pair",
        json={"token": raw, "remote_keys": _remote_keys()},
    )
    assert paired.status_code == 201, paired.text
    payload = paired.json()
    access_id = payload["context"]["access_id"]
    token = payload["access_token"]

    observed = {}

    def fake_process(db_arg, *, access, keyset, compact_jwe):
        observed["db"] = db_arg
        observed["access_id"] = access.public_id
        observed["keyset_access_id"] = keyset.access_id
        observed["blob"] = compact_jwe
        return "opaque-signed-encrypted-ack"

    monkeypatch.setattr(patient_companion_agenda, "process_remote_envelope", fake_process)

    response = focused_client.post(
        f"/api/patient-companion/contexts/{access_id}/agenda/remote-command",
        headers={"Authorization": f"Bearer {token}"},
        json={"blob": "opaque-signed-encrypted-command"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"blob": "opaque-signed-encrypted-ack"}
    assert observed["access_id"] == access_id
    assert observed["blob"] == "opaque-signed-encrypted-command"
    assert observed["keyset_access_id"] == db.query(PatientCompanionAccess).one().id
