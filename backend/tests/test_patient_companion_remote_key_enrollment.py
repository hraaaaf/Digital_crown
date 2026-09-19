from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import (
    PatientCompanionCabinetRemoteKey,
    PatientCompanionInvitation,
    PatientCompanionRemoteKeyset,
)
from backend.routers.patient_companion_common import manual_code_hash, token_hash
from backend.services.patient_companion_remote_crypto import generate_p256_keypair


def _pair(client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_pairing

    monkeypatch.setattr(patient_companion_pairing, "check_rate_limit", lambda *args, **kwargs: None)
    patient = models.Patient(
        numero_dossier="PCRTG-001",
        nom="Remote",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=dentiste.id,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    raw_token = "remote-gate-one-shot-token"
    invitation = PatientCompanionInvitation(
        employer_id=dentiste.id,
        patient_id=patient.id,
        token_hash=token_hash(raw_token),
        manual_code_hash=manual_code_hash("RTGG-0001-TEST"),
        recipient_type="local_bridge",
        recipient_hash=token_hash("remote-gate-placeholder"),
        relationship_type="SELF",
        created_by_user_id=dentiste.id,
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    db.add(invitation)
    db.commit()

    paired = client.post("/api/patient-companion/pair", json={"token": raw_token})
    assert paired.status_code == 201, paired.text
    return paired.json()


def _fake_protect(clear: bytes) -> bytes:
    return b"test-os-bound:" + clear[::-1]


def test_remote_public_keys_enroll_once_without_storing_patient_private_material(
    client, db, dentiste, monkeypatch
):
    from backend.routers import patient_companion_remote

    pairing = _pair(client, db, dentiste, monkeypatch)
    client.app.dependency_overrides[patient_companion_remote.get_remote_key_protector] = lambda: _fake_protect
    try:
        _sig_private, sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
        _enc_private, enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
        body = {
            "patient_signing_kid": sig_public["kid"],
            "patient_signing_public_jwk": sig_public,
            "patient_encryption_kid": enc_public["kid"],
            "patient_encryption_public_jwk": enc_public,
        }
        headers = {"Authorization": f"Bearer {pairing['access_token']}"}
        url = f"/api/patient-companion/contexts/{pairing['context']['access_id']}/remote-keys/enroll"

        enrolled = client.post(url, json=body, headers=headers)
        assert enrolled.status_code == 201, enrolled.text
        assert enrolled.headers["cache-control"] == "no-store"
        payload = enrolled.json()
        assert payload["protocol_version"] == "dc-pc-remote-v1"
        assert payload["patient_signing_kid"] == sig_public["kid"]
        assert payload["patient_encryption_kid"] == enc_public["kid"]
        assert "private" not in enrolled.text.lower()
        assert '"d"' not in enrolled.text

        keyset = db.query(PatientCompanionRemoteKeyset).one()
        assert '"d"' not in keyset.patient_signing_public_jwk_json
        assert '"d"' not in keyset.patient_encryption_public_jwk_json
        assert keyset.status == "ACTIVE"

        cabinet_rows = db.query(PatientCompanionCabinetRemoteKey).all()
        assert len(cabinet_rows) == 2
        for row in cabinet_rows:
            decoded = base64.urlsafe_b64decode(row.protected_private_jwk_b64.encode("ascii"))
            assert decoded.startswith(b"test-os-bound:")
            assert '"d"' not in row.public_jwk_json

        repeated = client.post(url, json=body, headers=headers)
        assert repeated.status_code == 409
    finally:
        client.app.dependency_overrides.pop(patient_companion_remote.get_remote_key_protector, None)


def test_remote_enrollment_rejects_patient_private_jwk(client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_remote

    pairing = _pair(client, db, dentiste, monkeypatch)
    client.app.dependency_overrides[patient_companion_remote.get_remote_key_protector] = lambda: _fake_protect
    try:
        sig_private, _sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
        _enc_private, enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
        headers = {"Authorization": f"Bearer {pairing['access_token']}"}
        url = f"/api/patient-companion/contexts/{pairing['context']['access_id']}/remote-keys/enroll"
        response = client.post(
            url,
            json={
                "patient_signing_kid": sig_private["kid"],
                "patient_signing_public_jwk": sig_private,
                "patient_encryption_kid": enc_public["kid"],
                "patient_encryption_public_jwk": enc_public,
            },
            headers=headers,
        )
        assert response.status_code == 422
        assert db.query(PatientCompanionRemoteKeyset).count() == 0
        assert db.query(PatientCompanionCabinetRemoteKey).count() == 0
    finally:
        client.app.dependency_overrides.pop(patient_companion_remote.get_remote_key_protector, None)
