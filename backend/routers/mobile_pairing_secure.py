"""Fail-closed mobile pairing against the signed cabinet device entitlement."""
from __future__ import annotations

import os
import uuid
from datetime import datetime

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend import database, models
from backend.security import ALGORITHM, SECRET_KEY
from backend.services.license_service import LicenseService
from . import mobile_legacy as _legacy

router = APIRouter()


def _license_identifier_for_employer(db: Session, employer_id: int) -> str:
    config = (
        db.query(models.CabinetConfig)
        .filter(models.CabinetConfig.owner_id == employer_id)
        .first()
    )
    if not config:
        raise HTTPException(status_code=409, detail="Cabinet non configuré : appairage refusé.")
    clinic_id = str(config.clinic_id or config.public_id or "").strip()
    if not clinic_id:
        raise HTTPException(status_code=409, detail="Identité de licence cabinet introuvable.")
    return clinic_id


def _device_limit_from_entitlement(effective: dict) -> int | None:
    if effective.get("active") is not True:
        raise HTTPException(status_code=402, detail="Licence signée active requise pour appairer un appareil.")

    license_type = str(effective.get("license_type") or "").upper()
    if license_type == "OWNER":
        # OWNER is the cryptographic commercial exemption and intentionally has
        # no max_devices claim in schema v1.
        return None

    max_devices = effective.get("max_devices")
    if isinstance(max_devices, bool) or not isinstance(max_devices, int) or max_devices < 1:
        raise HTTPException(
            status_code=503,
            detail="Entitlement appareil signé indisponible : appairage refusé.",
        )
    return max_devices


def _serialize_pairing_write(db: Session, employer_id: int) -> None:
    """Serialize capacity check + insert + token consume across concurrent claims."""
    db.rollback()
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        # Digital Crown cabinet runtime is SQLite. BEGIN IMMEDIATE reserves the
        # single writer before capacity is counted, preventing over-allocation.
        db.execute(text("BEGIN IMMEDIATE"))
        return

    # Future server-grade databases get a tenant-scoped row lock instead.
    locked = (
        db.query(models.CabinetConfig)
        .filter(models.CabinetConfig.owner_id == employer_id)
        .with_for_update()
        .first()
    )
    if not locked:
        raise HTTPException(status_code=409, detail="Cabinet non configuré : appairage refusé.")


def _active_device_count(db: Session, employer_id: int) -> int:
    return (
        db.query(models.MobilePairedDevice)
        .filter(
            models.MobilePairedDevice.employer_id == employer_id,
            models.MobilePairedDevice.revoked_at.is_(None),
        )
        .count()
    )


def _require_device_capacity(db: Session, employer_id: int, max_devices: int | None) -> int:
    active_count = _active_device_count(db, employer_id)
    if max_devices is not None and active_count >= max_devices:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "MOBILE_DEVICE_LIMIT_REACHED",
                "message": "Limite d'appareils de la licence signée atteinte.",
                "max_devices": max_devices,
                "active_devices": active_count,
            },
        )
    return active_count


def _build_ecdh_response(master_key: str, client_public_key_hex: str) -> tuple[str, str]:
    try:
        client_pub_bytes = bytes.fromhex(client_public_key_hex)
        client_public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), client_pub_bytes
        )
        server_private_key = ec.generate_private_key(ec.SECP256R1())
        server_public_key = server_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint,
        )
        shared_key = server_private_key.exchange(ec.ECDH(), client_public_key)
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b"zka_mobile_bridge",
        ).derive(shared_key)
        nonce = os.urandom(12)
        encrypted_master_key = AESGCM(derived_key).encrypt(nonce, master_key.encode(), None)
        return server_public_key.hex(), (nonce + encrypted_master_key).hex()
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Clé publique client invalide.") from exc


@router.post(
    "/claim-token",
    summary="Échanger un token éphémère QR contre un JWT mobile",
    description="Appairage ECDH one-shot, borné par max_devices de la licence signée.",
)
async def claim_pairing_token_secure(
    body: _legacy.ClaimTokenRequest,
    request: Request,
    db: Session = Depends(database.get_db),
):
    from backend.utils.rate_limit import check_rate_limit

    check_rate_limit(request, scope="mobile-pairing")
    now = datetime.utcnow()
    preliminary = (
        db.query(models.ZKAPairingToken)
        .filter(
            (
                (models.ZKAPairingToken.token == body.token)
                | (models.ZKAPairingToken.manual_code == body.token)
            ),
            models.ZKAPairingToken.used_at.is_(None),
            models.ZKAPairingToken.expires_at > now,
        )
        .first()
    )
    if not preliminary:
        raise HTTPException(status_code=404, detail="Token invalide, expiré ou déjà utilisé.")
    if not preliminary.user_id:
        raise HTTPException(
            status_code=409,
            detail="Ancien code d'appairage non compatible. Générez un nouveau QR.",
        )
    if not body.client_public_key_hex:
        raise HTTPException(
            status_code=400,
            detail="Appairage sécurisé requis : clé publique client (ECDH) manquante.",
        )

    employer_id = int(preliminary.employer_id)
    clinic_id = _license_identifier_for_employer(db, employer_id)
    effective = await LicenseService().get_effective_license(clinic_id)
    max_devices = _device_limit_from_entitlement(effective)

    # End the preliminary read transaction, then reserve the tenant write boundary.
    # The token is re-read afterwards so a concurrent claim cannot reuse stale state.
    _serialize_pairing_write(db, employer_id)
    now = datetime.utcnow()
    record = (
        db.query(models.ZKAPairingToken)
        .filter(
            (
                (models.ZKAPairingToken.token == body.token)
                | (models.ZKAPairingToken.manual_code == body.token)
            ),
            models.ZKAPairingToken.used_at.is_(None),
            models.ZKAPairingToken.expires_at > now,
            models.ZKAPairingToken.employer_id == employer_id,
        )
        .first()
    )
    if not record:
        db.rollback()
        raise HTTPException(status_code=409, detail="Token déjà utilisé ou expiré.")

    user = db.query(models.User).filter(models.User.id == record.user_id).first()
    if not user or not user.is_active or user.get_employer_id() != employer_id:
        db.rollback()
        raise HTTPException(status_code=403, detail="Utilisateur mobile non autorisé.")

    _require_device_capacity(db, employer_id, max_devices)
    role = user.role.value if hasattr(user.role, "value") else str(user.role)
    device_id = str(uuid.uuid4())
    access_token = _legacy._create_mobile_jwt(
        user.id,
        role,
        employer_id=employer_id,
        device_id=device_id,
    )
    refresh_token = _legacy._create_mobile_refresh_jwt(
        user.id,
        role,
        employer_id=employer_id,
        device_id=device_id,
    )
    refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    server_public_key_hex, encrypted_master_key_hex = _build_ecdh_response(
        record.master_key,
        body.client_public_key_hex,
    )

    db.add(
        models.MobilePairedDevice(
            device_id=device_id,
            user_id=user.id,
            employer_id=employer_id,
            client_public_key_hex=body.client_public_key_hex,
            refresh_jti=refresh_payload["jti"],
        )
    )
    consumed_at = datetime.utcnow()
    claimed = (
        db.query(models.ZKAPairingToken)
        .filter(
            models.ZKAPairingToken.id == record.id,
            models.ZKAPairingToken.used_at.is_(None),
            models.ZKAPairingToken.expires_at > consumed_at,
        )
        .update(
            {models.ZKAPairingToken.used_at: consumed_at},
            synchronize_session=False,
        )
    )
    if claimed != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Token déjà utilisé ou expiré.")

    db.commit()
    return {
        "publicId": record.public_id,
        "role": role,
        "user_id": user.id,
        "tenant_id": employer_id,
        "device_id": device_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "server_public_key_hex": server_public_key_hex,
        "encrypted_master_key_hex": encrypted_master_key_hex,
        "device_entitlement": {
            "max_devices": max_devices,
            "active_devices": _active_device_count(db, employer_id),
            "license_type": effective.get("license_type"),
        },
    }
