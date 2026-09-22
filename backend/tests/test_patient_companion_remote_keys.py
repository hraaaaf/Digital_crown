from __future__ import annotations

import os
import uuid
from datetime import datetime

import pytest

from backend import models
from backend.models_patient_companion import PatientCompanionAccess, PatientCompanionIdentity
from backend.services.patient_companion_key_protection import (
    OsKeyProtectionUnavailable,
    protect_os_bound,
    unprotect_os_bound,
)
from backend.services.patient_companion_remote_crypto import generate_p256_keypair
from backend.services.patient_companion_remote_keys import (
    enroll_remote_keyset,
    load_cabinet_private_jwk,
)


def _access(db, owner):
    patient = models.Patient(
        numero_dossier=f"PCRTG-{uuid.uuid4().hex[:8]}",
        nom="Remote",
        prenom="Aya",
        date_naissance=datetime(2010, 1, 1),
        sexe="F",
        employer_id=owner.id,
    )
    identity = PatientCompanionIdentity(
        provider="local_bridge",
        subject=f"device:{uuid.uuid4()}",
    )
    db.add_all([patient, identity])
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
    return access


def _fake_protect(clear: bytes) -> bytes:
    return b"protected-prefix:" + clear


def _fake_unprotect(value: bytes) -> bytes:
    return value.removeprefix(b"protected-prefix:")


def test_remote_key_enrollment_keeps_patient_material_public_only(db, dentiste):
    access = _access(db, dentiste)
    sig_kid = str(uuid.uuid4())
    enc_kid = str(uuid.uuid4())
    sig_secret, sig_public = generate_p256_keypair(kid=sig_kid, use="sig")
    _enc_secret, enc_public = generate_p256_keypair(kid=enc_kid, use="enc")

    keyset, cabinet_signing, cabinet_encryption = enroll_remote_keyset(
        db,
        access=access,
        patient_signing_kid=sig_kid,
        patient_signing_public_jwk=sig_public,
        patient_encryption_kid=enc_kid,
        patient_encryption_public_jwk=enc_public,
        protect=_fake_protect,
    )
    db.commit()

    assert keyset.status == "ACTIVE"
    assert '"d"' not in keyset.patient_signing_public_jwk_json
    assert '"d"' not in keyset.patient_encryption_public_jwk_json
    assert cabinet_signing.kid != cabinet_encryption.kid
    recovered = load_cabinet_private_jwk(cabinet_signing, unprotect=_fake_unprotect)
    assert "d" in recovered

    with pytest.raises(ValueError, match="private JWK"):
        enroll_remote_keyset(
            db,
            access=access,
            patient_signing_kid=sig_kid,
            patient_signing_public_jwk=sig_secret,
            patient_encryption_kid=enc_kid,
            patient_encryption_public_jwk=enc_public,
            protect=_fake_protect,
        )


@pytest.mark.skipif(os.name == "nt", reason="non-Windows fail-closed certification")
def test_os_key_protection_fails_closed_without_supported_provider():
    with pytest.raises(OsKeyProtectionUnavailable):
        protect_os_bound(b"cabinet-key")


@pytest.mark.skipif(os.name != "nt", reason="Windows DPAPI certification")
def test_windows_dpapi_os_bound_roundtrip():
    clear = b"cabinet-key-material"
    protected = protect_os_bound(clear)
    assert protected != clear
    assert clear not in protected
    assert unprotect_os_bound(protected) == clear
