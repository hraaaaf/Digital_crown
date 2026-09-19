from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime
from typing import Any, Callable

from jwcrypto import jwk
from sqlalchemy.orm import Session

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionCabinetRemoteKey,
    PatientCompanionRemoteKeyset,
)
from backend.services.patient_companion_key_protection import (
    protect_os_bound,
    unprotect_os_bound,
)
from backend.services.patient_companion_remote_crypto import generate_p256_keypair
from relay.contract import JOSE_JWE_ALG, JOSE_JWS_ALG

ProtectFn = Callable[[bytes], bytes]
UnprotectFn = Callable[[bytes], bytes]


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _decode_coordinate(value: str) -> bytes:
    try:
        padded = value + "=" * (-len(value) % 4)
        raw = base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception as exc:
        raise ValueError("invalid EC public JWK coordinate") from exc
    if len(raw) != 32:
        raise ValueError("P-256 public JWK coordinates must be 32 bytes")
    return raw


def normalize_patient_public_jwk(
    value: dict[str, Any],
    *,
    expected_use: str,
    expected_kid: str,
) -> dict[str, Any]:
    if expected_use not in {"sig", "enc"}:
        raise ValueError("invalid expected key use")
    try:
        uuid.UUID(expected_kid)
    except (ValueError, TypeError, AttributeError):
        raise ValueError("remote key id must be an opaque UUID") from None
    if not isinstance(value, dict):
        raise ValueError("public JWK must be an object")
    if "d" in value:
        raise ValueError("private JWK material is forbidden during enrollment")
    if value.get("kty") != "EC" or value.get("crv") != "P-256":
        raise ValueError("remote public JWK must be EC P-256")
    if not isinstance(value.get("x"), str) or not isinstance(value.get("y"), str):
        raise ValueError("remote public JWK coordinates are required")
    _decode_coordinate(value["x"])
    _decode_coordinate(value["y"])

    supplied_kid = value.get("kid")
    if supplied_kid is not None and supplied_kid != expected_kid:
        raise ValueError("public JWK kid mismatch")
    supplied_use = value.get("use")
    if supplied_use is not None and supplied_use != expected_use:
        raise ValueError("public JWK use mismatch")
    expected_alg = JOSE_JWS_ALG if expected_use == "sig" else JOSE_JWE_ALG
    supplied_alg = value.get("alg")
    if supplied_alg is not None and supplied_alg != expected_alg:
        raise ValueError("public JWK algorithm mismatch")

    key_ops = value.get("key_ops")
    if key_ops is not None:
        if not isinstance(key_ops, list) or not all(isinstance(item, str) for item in key_ops):
            raise ValueError("invalid public JWK key_ops")
        allowed_ops = {"verify"} if expected_use == "sig" else set()
        if not set(key_ops).issubset(allowed_ops):
            raise ValueError("public JWK key_ops exceed public-key use")

    normalized = {
        "kty": "EC",
        "crv": "P-256",
        "x": value["x"],
        "y": value["y"],
        "kid": expected_kid,
        "use": expected_use,
    }
    # Let the maintained JOSE implementation validate the normalized EC point.
    jwk.JWK.from_json(_json(normalized))
    return normalized


def ensure_active_cabinet_key(
    db: Session,
    *,
    employer_id: int,
    key_use: str,
    protect: ProtectFn = protect_os_bound,
) -> PatientCompanionCabinetRemoteKey:
    if key_use not in {"sig", "enc"}:
        raise ValueError("unsupported cabinet key use")
    existing = (
        db.query(PatientCompanionCabinetRemoteKey)
        .filter(
            PatientCompanionCabinetRemoteKey.employer_id == employer_id,
            PatientCompanionCabinetRemoteKey.key_use == key_use,
            PatientCompanionCabinetRemoteKey.status == "ACTIVE",
            PatientCompanionCabinetRemoteKey.revoked_at.is_(None),
        )
        .order_by(PatientCompanionCabinetRemoteKey.created_at.desc())
        .first()
    )
    if existing is not None:
        return existing

    kid = str(uuid.uuid4())
    private_jwk, public_jwk = generate_p256_keypair(kid=kid, use=key_use)
    protected = protect(_json(private_jwk).encode("utf-8"))
    row = PatientCompanionCabinetRemoteKey(
        employer_id=employer_id,
        kid=kid,
        key_use=key_use,
        public_jwk_json=_json(public_jwk),
        protected_private_jwk_b64=base64.urlsafe_b64encode(protected).decode("ascii"),
        status="ACTIVE",
    )
    db.add(row)
    db.flush()
    return row


def load_cabinet_private_jwk(
    key: PatientCompanionCabinetRemoteKey,
    *,
    unprotect: UnprotectFn = unprotect_os_bound,
) -> dict[str, Any]:
    if key.status == "REVOKED" or key.revoked_at is not None:
        raise ValueError("cabinet remote key is revoked")
    try:
        ciphertext = base64.urlsafe_b64decode(key.protected_private_jwk_b64.encode("ascii"))
        plaintext = unprotect(ciphertext)
        value = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise ValueError("unable to recover cabinet remote private key") from exc
    if not isinstance(value, dict) or "d" not in value:
        raise ValueError("invalid protected cabinet private JWK")
    return value


def enroll_remote_keyset(
    db: Session,
    *,
    access: PatientCompanionAccess,
    patient_signing_kid: str,
    patient_signing_public_jwk: dict[str, Any],
    patient_encryption_kid: str,
    patient_encryption_public_jwk: dict[str, Any],
    protect: ProtectFn = protect_os_bound,
) -> tuple[
    PatientCompanionRemoteKeyset,
    PatientCompanionCabinetRemoteKey,
    PatientCompanionCabinetRemoteKey,
]:
    signing_public = normalize_patient_public_jwk(
        patient_signing_public_jwk,
        expected_use="sig",
        expected_kid=patient_signing_kid,
    )
    encryption_public = normalize_patient_public_jwk(
        patient_encryption_public_jwk,
        expected_use="enc",
        expected_kid=patient_encryption_kid,
    )
    if patient_signing_kid == patient_encryption_kid:
        raise ValueError("signing and encryption keys must be independent")

    cabinet_signing = ensure_active_cabinet_key(
        db,
        employer_id=access.employer_id,
        key_use="sig",
        protect=protect,
    )
    cabinet_encryption = ensure_active_cabinet_key(
        db,
        employer_id=access.employer_id,
        key_use="enc",
        protect=protect,
    )
    if cabinet_signing.kid == cabinet_encryption.kid:
        raise ValueError("cabinet signing and encryption keys must be independent")

    now = datetime.utcnow()
    active_rows = (
        db.query(PatientCompanionRemoteKeyset)
        .filter(
            PatientCompanionRemoteKeyset.access_id == access.id,
            PatientCompanionRemoteKeyset.status == "ACTIVE",
            PatientCompanionRemoteKeyset.revoked_at.is_(None),
        )
        .all()
    )
    for row in active_rows:
        row.status = "RETIRED"
        row.retired_at = now

    keyset = PatientCompanionRemoteKeyset(
        access_id=access.id,
        patient_signing_kid=patient_signing_kid,
        patient_signing_public_jwk_json=_json(signing_public),
        patient_encryption_kid=patient_encryption_kid,
        patient_encryption_public_jwk_json=_json(encryption_public),
        cabinet_signing_kid=cabinet_signing.kid,
        cabinet_encryption_kid=cabinet_encryption.kid,
        status="ACTIVE",
    )
    db.add(keyset)
    db.flush()
    return keyset, cabinet_signing, cabinet_encryption


def public_keyset_response(
    keyset: PatientCompanionRemoteKeyset,
    cabinet_signing: PatientCompanionCabinetRemoteKey,
    cabinet_encryption: PatientCompanionCabinetRemoteKey,
) -> dict[str, Any]:
    return {
        "protocol_version": "dc-pc-remote-v1",
        "keyset_id": keyset.public_id,
        "patient_signing_kid": keyset.patient_signing_kid,
        "patient_encryption_kid": keyset.patient_encryption_kid,
        "cabinet": {
            "signing": {
                "kid": cabinet_signing.kid,
                "public_jwk": json.loads(cabinet_signing.public_jwk_json),
            },
            "encryption": {
                "kid": cabinet_encryption.kid,
                "public_jwk": json.loads(cabinet_encryption.public_jwk_json),
            },
        },
    }
