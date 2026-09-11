"""C2 encrypted content-addressed storage for ClinicalAsset.

Security contract:
- plaintext clinical bytes are never written to disk;
- storage keys use opaque tenant-scoped HMAC locators, never patient identity, original
  filename or the plaintext SHA-256 digest;
- SHA-256 is computed server-side from plaintext bytes and kept in the encrypted database;
- ciphertext is AES-GCM authenticated and bound to tenant + digest via AAD;
- deduplication is allowed only inside one tenant storage namespace;
- reads fail closed on tenant mismatch, path escape, missing data or integrity failure.

The caller owns the SQLAlchemy transaction. Files are written and verified before storage
metadata is flushed. A later DB rollback can therefore leave an encrypted, unreferenced
content-addressed blob, but cannot leave a committed asset pointing at an unverified write.
Future garbage collection may remove such unreferenced blobs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import os
from pathlib import Path, PurePosixPath
import uuid
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from sqlalchemy.orm import Session

from backend.core.media_paths import get_media_root
from backend.models_media_core import (
    CLINICAL_ASSET_STORAGE_FORMAT_AESGCM_V1,
    ClinicalAsset,
)
from backend.services.clinical_asset_service import get_clinical_asset_for_patient


_MAGIC = b"DCM1"
_NONCE_SIZE = 12
_STORAGE_PREFIX = "clinical-assets"
_KEY_INFO = b"digital-crown-clinical-media-aesgcm-v1"
_KEY_SALT = b"digital-crown-media-storage-v1"


class ClinicalAssetStorageError(RuntimeError):
    """Base error for storage contract violations or unavailable storage."""


class ClinicalAssetIntegrityError(ClinicalAssetStorageError):
    """Raised when encrypted media cannot be authenticated or verified."""


@dataclass(frozen=True)
class ClinicalAssetStoreResult:
    asset: ClinicalAsset
    deduplicated: bool


def _master_key_material() -> bytes:
    raw = (os.environ.get("CABINET_MASTER_KEY_HEX") or os.environ.get("SECRET_KEY") or "").strip()
    if not raw:
        raise ClinicalAssetStorageError("clinical media encryption key is unavailable")

    # Production/cabinet commonly provides a hex master key. Tests/dev may provide a
    # textual SECRET_KEY. Both are fed through HKDF so raw application secrets are never
    # used directly as AES/HMAC keys.
    try:
        material = bytes.fromhex(raw)
        if not material:
            raise ValueError
    except ValueError:
        material = raw.encode("utf-8")
    return material


def _media_encryption_key() -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KEY_SALT,
        info=_KEY_INFO,
    ).derive(_master_key_material())


def _aad(employer_id: int, digest: str) -> bytes:
    return f"digital-crown-media-v1:{int(employer_id)}:{digest}".encode("ascii")


def _opaque_locator(label: str) -> str:
    return hmac.new(
        _media_encryption_key(),
        label.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def _tenant_storage_token(employer_id: int) -> str:
    return _opaque_locator(f"tenant:{int(employer_id)}")[:24]


def _blob_storage_token(employer_id: int, digest: str) -> str:
    return _opaque_locator(f"blob:{int(employer_id)}:{digest}")


def _storage_key(employer_id: int, digest: str) -> str:
    tenant_token = _tenant_storage_token(employer_id)
    blob_token = _blob_storage_token(employer_id, digest)
    return f"{_STORAGE_PREFIX}/t-{tenant_token}/{blob_token[:2]}/{blob_token}.dcm"


def _validate_storage_key_for_tenant(storage_key: str, employer_id: int) -> None:
    if not storage_key or "\x00" in storage_key or "\\" in storage_key:
        raise ClinicalAssetStorageError("invalid clinical media storage key")
    pure = PurePosixPath(storage_key)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ClinicalAssetStorageError("invalid clinical media storage key")
    expected = (_STORAGE_PREFIX, f"t-{_tenant_storage_token(employer_id)}")
    if len(pure.parts) != 4 or tuple(pure.parts[:2]) != expected:
        raise ClinicalAssetStorageError("clinical media storage key is outside tenant namespace")


def _resolve_storage_path(storage_key: str, employer_id: int, media_root: Optional[Path]) -> tuple[Path, Path]:
    _validate_storage_key_for_tenant(storage_key, employer_id)
    root = Path(media_root) if media_root is not None else get_media_root()
    root = root.expanduser().resolve(strict=False)
    target = root.joinpath(*PurePosixPath(storage_key).parts).resolve(strict=False)
    if target != root and root not in target.parents:
        raise ClinicalAssetStorageError("clinical media path escapes MEDIA_ROOT")
    return root, target


def _ensure_private_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path, 0o700)
    except OSError:
        # Windows ACLs are governed by the app data directory/platform adapter.
        pass


def _prepare_parent_directory(root: Path, target: Path) -> None:
    _ensure_private_directory(root)
    current = root
    relative_parent = target.parent.relative_to(root)
    for part in relative_parent.parts:
        current = current / part
        if current.is_symlink():
            raise ClinicalAssetStorageError("clinical media storage directory cannot be a symlink")
        _ensure_private_directory(current)
        resolved = current.resolve(strict=False)
        if resolved != root and root not in resolved.parents:
            raise ClinicalAssetStorageError("clinical media storage directory escapes MEDIA_ROOT")


def _encrypt_payload(plaintext: bytes, employer_id: int, digest: str) -> bytes:
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(_media_encryption_key()).encrypt(nonce, plaintext, _aad(employer_id, digest))
    return _MAGIC + nonce + ciphertext


def _decrypt_payload(payload: bytes, employer_id: int, digest: str) -> bytes:
    if len(payload) <= len(_MAGIC) + _NONCE_SIZE or payload[: len(_MAGIC)] != _MAGIC:
        raise ClinicalAssetIntegrityError("clinical media blob has an invalid storage envelope")
    nonce_start = len(_MAGIC)
    nonce = payload[nonce_start : nonce_start + _NONCE_SIZE]
    ciphertext = payload[nonce_start + _NONCE_SIZE :]
    try:
        return AESGCM(_media_encryption_key()).decrypt(nonce, ciphertext, _aad(employer_id, digest))
    except InvalidTag as exc:
        raise ClinicalAssetIntegrityError("clinical media authentication failed") from exc


def _atomic_write(target: Path, payload: bytes) -> None:
    if target.is_symlink():
        raise ClinicalAssetStorageError("clinical media target cannot be a symlink")
    temp_path = target.parent / f".tmp-{uuid.uuid4().hex}-{target.name}"
    fd = None
    try:
        fd = os.open(str(temp_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            fd = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
    finally:
        if fd is not None:
            os.close(fd)
        if temp_path.exists():
            temp_path.unlink()


def _read_verified_path(path: Path, *, employer_id: int, digest: str, byte_size: int) -> bytes:
    if path.is_symlink():
        raise ClinicalAssetIntegrityError("clinical media blob cannot be a symlink")
    if not path.is_file():
        raise ClinicalAssetIntegrityError("clinical media blob is missing")
    plaintext = _decrypt_payload(path.read_bytes(), employer_id, digest)
    actual_digest = hashlib.sha256(plaintext).hexdigest()
    if actual_digest != digest or len(plaintext) != int(byte_size):
        raise ClinicalAssetIntegrityError("clinical media plaintext integrity check failed")
    return plaintext


def store_clinical_asset_bytes(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    asset_id: int,
    content: bytes,
    media_root: Optional[Path] = None,
) -> ClinicalAssetStoreResult:
    """Encrypt, atomically store and bind bytes to an existing tenant-scoped asset.

    Deduplication is physical and tenant-scoped: identical plaintext inside one tenant maps
    to the same opaque content-addressed storage key. Different tenants always map to
    different HMAC namespaces and AES-GCM AAD domains, even when plaintext is identical.
    """
    employer_id = int(employer_id)
    patient_id = int(patient_id)
    asset_id = int(asset_id)

    if isinstance(content, (bytearray, memoryview)):
        content = bytes(content)
    if not isinstance(content, bytes) or not content:
        raise ClinicalAssetStorageError("clinical media content must be non-empty bytes")

    asset = get_clinical_asset_for_patient(
        db,
        employer_id=employer_id,
        patient_id=patient_id,
        asset_id=asset_id,
    )
    if asset is None:
        raise ClinicalAssetStorageError("clinical asset not found in tenant/patient scope")

    digest = hashlib.sha256(content).hexdigest()
    byte_size = len(content)
    storage_key = _storage_key(employer_id, digest)
    root, target = _resolve_storage_path(storage_key, employer_id, media_root)
    _prepare_parent_directory(root, target)

    deduplicated = target.exists()
    if target.is_symlink():
        raise ClinicalAssetIntegrityError("clinical media blob cannot be a symlink")

    if deduplicated:
        existing = _read_verified_path(
            target,
            employer_id=employer_id,
            digest=digest,
            byte_size=byte_size,
        )
        if existing != content:
            # Defensive collision/corruption guard beyond the SHA-256 comparison.
            raise ClinicalAssetIntegrityError("clinical media dedupe candidate does not match source bytes")
    else:
        _atomic_write(target, _encrypt_payload(content, employer_id, digest))
        stored = _read_verified_path(
            target,
            employer_id=employer_id,
            digest=digest,
            byte_size=byte_size,
        )
        if stored != content:
            raise ClinicalAssetIntegrityError("clinical media write verification failed")

    # DB metadata is changed only after the physical blob has passed authenticated readback.
    # If flush/commit later fails, the safe failure is an encrypted unreferenced blob.
    asset.sha256 = digest
    asset.byte_size = byte_size
    asset.storage_key = storage_key
    asset.storage_format = CLINICAL_ASSET_STORAGE_FORMAT_AESGCM_V1
    asset.stored_at = datetime.utcnow()
    db.flush()

    return ClinicalAssetStoreResult(asset=asset, deduplicated=deduplicated)


def read_clinical_asset_bytes(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    asset_id: int,
    media_root: Optional[Path] = None,
) -> bytes:
    """Return verified plaintext only after tenant scope + AES-GCM + SHA-256 checks pass."""
    employer_id = int(employer_id)
    asset = get_clinical_asset_for_patient(
        db,
        employer_id=employer_id,
        patient_id=int(patient_id),
        asset_id=int(asset_id),
    )
    if asset is None:
        raise ClinicalAssetStorageError("clinical asset not found in tenant/patient scope")
    if (
        not asset.storage_key
        or asset.storage_format != CLINICAL_ASSET_STORAGE_FORMAT_AESGCM_V1
        or not asset.sha256
        or asset.byte_size is None
    ):
        raise ClinicalAssetStorageError("clinical asset has no complete C2 storage binding")

    _root, target = _resolve_storage_path(asset.storage_key, employer_id, media_root)
    return _read_verified_path(
        target,
        employer_id=employer_id,
        digest=asset.sha256,
        byte_size=asset.byte_size,
    )


def verify_clinical_asset_storage(
    db: Session,
    *,
    employer_id: int,
    patient_id: int,
    asset_id: int,
    media_root: Optional[Path] = None,
) -> bool:
    """Explicit integrity probe used by future imports/maintenance and certification."""
    read_clinical_asset_bytes(
        db,
        employer_id=employer_id,
        patient_id=patient_id,
        asset_id=asset_id,
        media_root=media_root,
    )
    return True
