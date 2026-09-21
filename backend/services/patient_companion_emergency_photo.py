from __future__ import annotations

import base64
import binascii
import hashlib
import re
import uuid
import os
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from backend.models_patient_companion import (
    PatientCompanionAccess,
    PatientCompanionEmergencyPhotoChunk,
    PatientCompanionEmergencyPhotoUpload,
)
from backend.services.clinical_asset_ingestion import (
    ClinicalAssetIngestionError,
    ingest_clinical_asset_bytes,
)
from backend.services.clinical_asset_service import ClinicalAssetInvariantError
from backend.services.clinical_asset_storage import ClinicalAssetStorageError
from backend.services.clinical_photo_normalization import (
    CLINICAL_PHOTO_MAX_BYTES,
    normalize_clinical_photo,
)
from backend.services.patient_companion_remote_worker import RemoteDomainResult

PC07_CHUNK_BYTES = 96 * 1024
PC07_MAX_CHUNKS = CLINICAL_PHOTO_MAX_BYTES // PC07_CHUNK_BYTES
PC07_UPLOAD_TTL = timedelta(hours=24)
PC07_MAX_ACTIVE_UPLOADS_PER_ACCESS = 3
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ASSEMBLY_MAGIC = b"PC07C1"
_ASSEMBLY_SALT = b"digital-crown-pc07-assembly-v1"
_ASSEMBLY_INFO = b"digital-crown-pc07-chunk-aesgcm-v1"


def _assembly_master_material() -> bytes:
    raw = (os.environ.get("CABINET_MASTER_KEY_HEX") or os.environ.get("SECRET_KEY") or "").strip()
    if not raw:
        raise ClinicalAssetStorageError("PC-07 assembly encryption key is unavailable")
    try:
        material = bytes.fromhex(raw)
        if not material:
            raise ValueError
    except ValueError:
        material = raw.encode("utf-8")
    return material


def _assembly_key() -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_ASSEMBLY_SALT,
        info=_ASSEMBLY_INFO,
    ).derive(_assembly_master_material())


def _chunk_aad(access_id: int, upload_id: str, chunk_index: int) -> bytes:
    return f"dc-pc07-chunk:{int(access_id)}:{upload_id}:{int(chunk_index)}".encode("ascii")


def _encrypt_chunk(raw: bytes, *, access_id: int, upload_id: str, chunk_index: int) -> bytes:
    nonce = os.urandom(12)
    encrypted = AESGCM(_assembly_key()).encrypt(
        nonce,
        raw,
        _chunk_aad(access_id, upload_id, chunk_index),
    )
    return _ASSEMBLY_MAGIC + nonce + encrypted


def _decrypt_chunk(payload: bytes, *, access_id: int, upload_id: str, chunk_index: int) -> bytes:
    if not payload.startswith(_ASSEMBLY_MAGIC) or len(payload) <= len(_ASSEMBLY_MAGIC) + 12:
        raise ClinicalAssetStorageError("PC-07 temporary chunk envelope invalid")
    offset = len(_ASSEMBLY_MAGIC)
    nonce = payload[offset:offset + 12]
    ciphertext = payload[offset + 12:]
    try:
        return AESGCM(_assembly_key()).decrypt(
            nonce,
            ciphertext,
            _chunk_aad(access_id, upload_id, chunk_index),
        )
    except Exception as exc:
        raise ClinicalAssetStorageError("PC-07 temporary chunk authentication failed") from exc




def _reject(code: str) -> RemoteDomainResult:
    return RemoteDomainResult(status="REJECTED", response={"code": code})


def _accepted(**response) -> RemoteDomainResult:
    return RemoteDomainResult(status="ACCEPTED", response=response)


def _valid_uuid(raw) -> str | None:
    try:
        return str(uuid.UUID(str(raw)))
    except (TypeError, ValueError, AttributeError):
        return None


def _valid_sha(raw) -> str | None:
    value = str(raw or "").lower()
    return value if _SHA256_RE.fullmatch(value) else None


def _captured_at(raw) -> datetime | None:
    if raw in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.replace(tzinfo=None) if parsed.tzinfo is not None else parsed


def _purge_expired(db: Session) -> None:
    now = datetime.utcnow()
    expired_ids = [
        row[0]
        for row in db.query(PatientCompanionEmergencyPhotoUpload.id).filter(
            PatientCompanionEmergencyPhotoUpload.status == "UPLOADING",
            PatientCompanionEmergencyPhotoUpload.expires_at <= now,
        ).all()
    ]
    if not expired_ids:
        return
    db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id.in_(expired_ids)
    ).delete(synchronize_session=False)
    db.query(PatientCompanionEmergencyPhotoUpload).filter(
        PatientCompanionEmergencyPhotoUpload.id.in_(expired_ids)
    ).delete(synchronize_session=False)
    db.flush()


def _upload(db: Session, access: PatientCompanionAccess, public_id: str):
    return db.query(PatientCompanionEmergencyPhotoUpload).filter(
        PatientCompanionEmergencyPhotoUpload.access_id == access.id,
        PatientCompanionEmergencyPhotoUpload.public_id == public_id,
        PatientCompanionEmergencyPhotoUpload.employer_id == access.employer_id,
        PatientCompanionEmergencyPhotoUpload.patient_id == access.patient_id,
    ).first()


def begin_emergency_photo(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict,
) -> RemoteDomainResult:
    allowed = {"upload_id", "object_sha256", "byte_size", "chunk_count", "captured_at"}
    if not isinstance(payload, dict) or set(payload) - allowed:
        return _reject("INVALID_REQUEST")

    upload_id = _valid_uuid(payload.get("upload_id"))
    object_sha256 = _valid_sha(payload.get("object_sha256"))
    captured_at = _captured_at(payload.get("captured_at"))
    try:
        byte_size = int(payload.get("byte_size"))
        chunk_count = int(payload.get("chunk_count"))
    except (TypeError, ValueError):
        return _reject("INVALID_REQUEST")

    if (
        not upload_id
        or not object_sha256
        or byte_size <= 0
        or byte_size > CLINICAL_PHOTO_MAX_BYTES
        or chunk_count <= 0
        or chunk_count > PC07_MAX_CHUNKS
        or chunk_count != (byte_size + PC07_CHUNK_BYTES - 1) // PC07_CHUNK_BYTES
        or (payload.get("captured_at") not in (None, "") and captured_at is None)
    ):
        return _reject("INVALID_REQUEST")

    _purge_expired(db)
    existing = _upload(db, access, upload_id)
    if existing is not None:
        if (
            existing.object_sha256 != object_sha256
            or existing.byte_size != byte_size
            or existing.chunk_count != chunk_count
        ):
            return _reject("UPLOAD_CONFLICT")
        if existing.status == "RECEIVED" and existing.asset_id is not None:
            return _accepted(
                state="received",
                upload_id=upload_id,
                asset_id=int(existing.asset_id),
            )
        indices = [
            row[0]
            for row in db.query(PatientCompanionEmergencyPhotoChunk.chunk_index).filter(
                PatientCompanionEmergencyPhotoChunk.upload_id == existing.id
            ).order_by(PatientCompanionEmergencyPhotoChunk.chunk_index.asc()).all()
        ]
        contiguous_prefix = 0
        for index in indices:
            if index != contiguous_prefix:
                break
            contiguous_prefix += 1
        return _accepted(
            state="uploading",
            upload_id=upload_id,
            received_chunks=contiguous_prefix,
            chunk_count=existing.chunk_count,
        )

    active_uploads = db.query(PatientCompanionEmergencyPhotoUpload).filter(
        PatientCompanionEmergencyPhotoUpload.access_id == access.id,
        PatientCompanionEmergencyPhotoUpload.status == "UPLOADING",
        PatientCompanionEmergencyPhotoUpload.expires_at > datetime.utcnow(),
    ).count()
    if active_uploads >= PC07_MAX_ACTIVE_UPLOADS_PER_ACCESS:
        return _reject("TOO_MANY_ACTIVE_UPLOADS")

    now = datetime.utcnow()
    row = PatientCompanionEmergencyPhotoUpload(
        public_id=upload_id,
        access_id=access.id,
        employer_id=access.employer_id,
        patient_id=access.patient_id,
        object_sha256=object_sha256,
        byte_size=byte_size,
        chunk_count=chunk_count,
        captured_at=captured_at,
        status="UPLOADING",
        created_at=now,
        updated_at=now,
        expires_at=now + PC07_UPLOAD_TTL,
    )
    db.add(row)
    db.flush()
    return _accepted(
        state="uploading",
        upload_id=upload_id,
        received_chunks=0,
        chunk_count=chunk_count,
    )


def submit_emergency_photo_chunk(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict,
) -> RemoteDomainResult:
    allowed = {"upload_id", "chunk_index", "chunk_sha256", "chunk_b64"}
    if not isinstance(payload, dict) or set(payload) != allowed:
        return _reject("INVALID_REQUEST")

    upload_id = _valid_uuid(payload.get("upload_id"))
    chunk_sha256 = _valid_sha(payload.get("chunk_sha256"))
    try:
        chunk_index = int(payload.get("chunk_index"))
    except (TypeError, ValueError):
        return _reject("INVALID_REQUEST")
    encoded = payload.get("chunk_b64")
    if not upload_id or not chunk_sha256 or not isinstance(encoded, str) or not encoded:
        return _reject("INVALID_REQUEST")

    _purge_expired(db)
    upload = _upload(db, access, upload_id)
    if upload is None:
        return _reject("UPLOAD_NOT_FOUND")
    if upload.status == "RECEIVED":
        return _accepted(state="received", upload_id=upload_id, asset_id=int(upload.asset_id))
    if chunk_index < 0 or chunk_index >= upload.chunk_count:
        return _reject("INVALID_CHUNK_INDEX")

    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        return _reject("INVALID_CHUNK_ENCODING")
    expected_max = PC07_CHUNK_BYTES
    if chunk_index == upload.chunk_count - 1:
        expected_max = upload.byte_size - (PC07_CHUNK_BYTES * (upload.chunk_count - 1))
    if not raw or len(raw) > PC07_CHUNK_BYTES or len(raw) != expected_max:
        return _reject("INVALID_CHUNK_SIZE")
    if hashlib.sha256(raw).hexdigest() != chunk_sha256:
        return _reject("CHUNK_DIGEST_MISMATCH")

    existing = db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id,
        PatientCompanionEmergencyPhotoChunk.chunk_index == chunk_index,
    ).first()
    if existing is not None:
        try:
            existing_raw = _decrypt_chunk(
                bytes(existing.content),
                access_id=access.id,
                upload_id=upload.public_id,
                chunk_index=chunk_index,
            )
        except ClinicalAssetStorageError:
            return _reject("STORAGE_UNAVAILABLE")
        if existing.chunk_sha256 != chunk_sha256 or existing_raw != raw:
            return _reject("CHUNK_CONFLICT")
    else:
        try:
            encrypted = _encrypt_chunk(
                raw,
                access_id=access.id,
                upload_id=upload.public_id,
                chunk_index=chunk_index,
            )
        except ClinicalAssetStorageError:
            return _reject("STORAGE_UNAVAILABLE")
        db.add(PatientCompanionEmergencyPhotoChunk(
            upload_id=upload.id,
            chunk_index=chunk_index,
            chunk_sha256=chunk_sha256,
            content=encrypted,
        ))
        upload.updated_at = datetime.utcnow()
        db.flush()

    received = db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id
    ).count()
    return _accepted(
        state="uploading",
        upload_id=upload_id,
        received_chunks=received,
        chunk_count=upload.chunk_count,
    )


def finalize_emergency_photo(
    db: Session,
    access: PatientCompanionAccess,
    payload: dict,
) -> RemoteDomainResult:
    if not isinstance(payload, dict) or set(payload) != {"upload_id"}:
        return _reject("INVALID_REQUEST")
    upload_id = _valid_uuid(payload.get("upload_id"))
    if not upload_id:
        return _reject("INVALID_REQUEST")

    _purge_expired(db)
    upload = _upload(db, access, upload_id)
    if upload is None:
        return _reject("UPLOAD_NOT_FOUND")
    if upload.status == "RECEIVED" and upload.asset_id is not None:
        return _accepted(
            state="received",
            upload_id=upload_id,
            asset_id=int(upload.asset_id),
            received_at=upload.completed_at.isoformat() if upload.completed_at else None,
        )

    chunks = db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id
    ).order_by(PatientCompanionEmergencyPhotoChunk.chunk_index.asc()).all()
    if len(chunks) != upload.chunk_count:
        return _reject("UPLOAD_INCOMPLETE")
    if [chunk.chunk_index for chunk in chunks] != list(range(upload.chunk_count)):
        return _reject("UPLOAD_INCOMPLETE")

    try:
        raw = b"".join(
            _decrypt_chunk(
                bytes(chunk.content),
                access_id=access.id,
                upload_id=upload.public_id,
                chunk_index=chunk.chunk_index,
            )
            for chunk in chunks
        )
    except ClinicalAssetStorageError:
        return _reject("STORAGE_UNAVAILABLE")
    if len(raw) != upload.byte_size:
        return _reject("OBJECT_SIZE_MISMATCH")
    if hashlib.sha256(raw).hexdigest() != upload.object_sha256:
        return _reject("OBJECT_DIGEST_MISMATCH")

    try:
        normalized = normalize_clinical_photo(raw)
        result = ingest_clinical_asset_bytes(
            db,
            employer_id=int(access.employer_id),
            patient_id=int(access.patient_id),
            asset_type="PHOTO",
            source_kind="DEVICE_CAPTURE",
            content=normalized,
            original_filename=f"patient-emergency-{upload.public_id}.jpg",
            claimed_mime_type="image/jpeg",
            source_ref="PATIENT_COMPANION_EMERGENCY_PHOTO",
            captured_at=upload.captured_at,
            created_by=None,
            provenance_json={
                "ingestion_channel": "PATIENT_COMPANION",
                "capture_kind": "EMERGENCY_PHOTO",
                "upload_id": upload.public_id,
            },
        )
    except HTTPException as exc:
        return _reject("IMAGE_TOO_LARGE" if exc.status_code == 413 else "INVALID_IMAGE")
    except (ClinicalAssetIngestionError, ClinicalAssetInvariantError):
        return _reject("INVALID_IMAGE")
    except (ClinicalAssetStorageError, OSError):
        return _reject("STORAGE_UNAVAILABLE")

    now = datetime.utcnow()
    upload.asset_id = result.asset.id
    upload.status = "RECEIVED"
    upload.completed_at = now
    upload.updated_at = now
    db.query(PatientCompanionEmergencyPhotoChunk).filter(
        PatientCompanionEmergencyPhotoChunk.upload_id == upload.id
    ).delete(synchronize_session=False)
    db.flush()

    return _accepted(
        state="received",
        upload_id=upload.public_id,
        asset_id=int(result.asset.id),
        received_at=now.isoformat(),
    )


PC07_REMOTE_HANDLERS = {
    "emergency_photo.begin": begin_emergency_photo,
    "emergency_photo.chunk": submit_emergency_photo_chunk,
    "emergency_photo.finalize": finalize_emergency_photo,
}
