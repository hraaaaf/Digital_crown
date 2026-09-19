from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from backend import models
from backend.models_patient_companion import PatientCompanionRemoteKeySet
from backend.routers.patient_companion_common import manual_code_hash, token_hash
from backend.models_patient_companion import PatientCompanionInvitation
from backend.services.patient_companion_remote_crypto import generate_p256_keypair


class _FakeCabinetVault:
    def __init__(self):
        signing_private, signing_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
        encryption_private, encryption_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
        self._bundle = {
            "version": 1,
            "signing": {"kid": signing_public["kid"], "public_jwk": signing_public},
            "encryption": {"kid": encryption_public["kid"], "public_jwk": encryption_public},
        }
        # Keep private variables local to the fake; response must never contain them.
        self._private = (signing_private, encryption_private)

    def public_bundle(self):
        return self._bundle


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


def test_remote_public_keys_enroll_once_and_return_only_cabinet_public_keys(client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_remote

    pairing = _pair(client, db, dentiste, monkeypatch)
    fake_vault = _FakeCabinetVault()
    client.app.dependency_overrides[patient_companion_remote.get_cabinet_remote_key_vault] = lambda: fake_vault
    try:
        _sig_private, sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
        _enc_private, enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
        body = {"signing": sig_public, "encryption": enc_public}
        headers = {"Authorization": f"Bearer {pairing['access_token']}"}
        url = f"/api/patient-companion/contexts/{pairing['context']['access_id']}/remote-keys/enroll"

        enrolled = client.post(url, json=body, headers=headers)
        assert enrolled.status_code == 201, enrolled.text
        payload = enrolled.json()
        assert payload["protocol_version"] == "dc-pc-remote-v1"
        assert payload["patient_signing_kid"] == sig_public["kid"]
        assert payload["patient_encryption_kid"] == enc_public["kid"]
        assert "private_jwk" not in enrolled.text
        assert '"d"' not in enrolled.text
        assert payload["cabinet_keys"] == fake_vault.public_bundle()

        row = db.query(PatientCompanionRemoteKeySet).one()
        assert '"d"' not in row.signing_public_jwk
        assert '"d"' not in row.encryption_public_jwk
        assert row.state == "ACTIVE"

        repeated = client.post(url, json=body, headers=headers)
        assert repeated.status_code == 409
    finally:
        client.app.dependency_overrides.pop(patient_companion_remote.get_cabinet_remote_key_vault, None)


def test_remote_key_enrollment_rejects_private_jwk_material(client, db, dentiste, monkeypatch):
    from backend.routers import patient_companion_remote

    pairing = _pair(client, db, dentiste, monkeypatch)
    client.app.dependency_overrides[patient_companion_remote.get_cabinet_remote_key_vault] = lambda: _FakeCabinetVault()
    try:
        sig_private, _sig_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
        _enc_private, enc_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")
        headers = {"Authorization": f"Bearer {pairing['access_token']}"}
        url = f"/api/patient-companion/contexts/{pairing['context']['access_id']}/remote-keys/enroll"
        response = client.post(
            url,
            json={"signing": sig_private, "encryption": enc_public},
            headers=headers,
        )
        assert response.status_code == 422
    finally:
        client.app.dependency_overrides.pop(patient_companion_remote.get_cabinet_remote_key_vault, None)
