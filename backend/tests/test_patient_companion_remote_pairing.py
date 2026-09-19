from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionInvitation,
    PatientCompanionRemoteKeyset,
)
from backend.routers.patient_companion_common import manual_code_hash, token_hash
from backend.services.patient_companion_key_protection import OsKeyProtectionUnavailable
from backend.services.patient_companion_remote_crypto import generate_p256_keypair
from backend.services.patient_companion_remote_keys import enroll_remote_keyset as real_enroll


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


def test_qr_pairing_atomically_enrolls_remote_public_keys(client, db, dentiste, monkeypatch):
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
    response = client.post(
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


def test_qr_pairing_rolls_back_when_os_key_protection_is_unavailable(client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)

    def fail_enrollment(*args, **kwargs):
        raise OsKeyProtectionUnavailable("test unavailable")

    monkeypatch.setattr(patient_companion_pairing, "enroll_remote_keyset", fail_enrollment)
    raw, invitation = _invitation(db, dentiste, "0002")

    response = client.post(
        "/api/patient-companion/pair",
        json={"token": raw, "remote_keys": _remote_keys()},
    )
    assert response.status_code == 503
    assert db.query(PatientCompanionAccess).count() == 0
    assert db.query(PatientCompanionRemoteKeyset).count() == 0
    db.refresh(invitation)
    assert invitation.consumed_at is None
