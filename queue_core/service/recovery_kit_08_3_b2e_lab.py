"""LOT08.3-B2-E: sealed, separately witnessed synthetic Queue recovery kit.

LAB-ONLY proof of confidential local custody and loss-of-workspace recovery.
No Windows DPAPI/TPM/escrow, offsite medium, production integration, scheduler,
real cabinet data, clinical restore, physical crash or RPO/RTO certification.

A SHA-256 witness MUST be retained independently of BOTH the kit and vault.
A stale witness blocks restore. Rolling back all three defeats this LAB model.
"""
from __future__ import annotations

from base64 import b64decode, b64encode
from binascii import Error as Base64DecodeError
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path
import hmac
import json
import os
import tempfile
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from queue_core.service.backup_restore_clone_08_3_b2_lab import (
    RestoreCloneLabError, _fernet, _now_epoch,
)
from queue_core.service.backup_rotation_08_3_b2c_lab import (
    _DIGEST_RE, _canonical, _keys, _read_catalog, _vault_folder,
    restore_queue_vault_clone_lab,
)

_KIT_FILE = "sealed-recovery-kit.aead.json"
_AAD = b"LOT08_3_B2E_SYNTHETIC_OFFLINE_RECOVERY_V1"
_MAX_KIT_SIZE = 8192
_SALT_SIZE = 16
_NONCE_SIZE = 12


@dataclass(frozen=True, slots=True)
class LabKitReceipt:
    witness_fingerprint: str
    generation: int


def _before_kit_publish_lab() -> None:
    """Fault-injection hook before create-only or atomic kit publication."""


def _kit_folder(value: str | Path, vault: Path) -> Path:
    try:
        original = Path(value)
        folder = original.resolve(strict=True)
        root = Path(tempfile.gettempdir()).resolve()
    except (OSError, TypeError, ValueError):
        raise RestoreCloneLabError("KIT_SYNTHETIC_FOLDER_REQUIRED") from None
    if (original.is_symlink() or not folder.is_dir()
        or not folder.is_relative_to(root) or folder.parent == root
        or not folder.name.startswith("lot08_3_b_lab_kit_")
        or folder == vault or folder.is_relative_to(vault)
        or vault.is_relative_to(folder)):
        raise RestoreCloneLabError("KIT_SYNTHETIC_FOLDER_REQUIRED")
    return folder


def _passphrase(passphrase: bytes) -> bytes:
    # This bound does not establish adequate human-created passphrase entropy.
    if not isinstance(passphrase, bytes) or not 24 <= len(passphrase) <= 1024:
        raise RestoreCloneLabError("KIT_HIGH_ENTROPY_PASSPHRASE_REQUIRED")
    return passphrase


def _derive(passphrase: bytes, salt: bytes) -> bytes:
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(
        _passphrase(passphrase)
    )


def _b64(data: bytes) -> str:
    return b64encode(data).decode("ascii")


def _unb64(value: object, length: int | None = None) -> bytes:
    if type(value) is not str:
        raise ValueError("not encoded")
    try:
        result = b64decode(value.encode("ascii"), validate=True)
    except (UnicodeError, ValueError, Base64DecodeError):
        raise ValueError("base64") from None
    if length is not None and len(result) != length:
        raise ValueError("length")
    return result


def _kit_path(folder: Path, *, exists: bool) -> Path:
    path = folder / _KIT_FILE
    if (path.is_symlink() or path.exists() != exists
        or (exists and not path.is_file())):
        raise RestoreCloneLabError("KIT_STATE_INVALID")
    return path


def _current_catalog(
    vault: Path, backup_key: bytes, manifest_key: bytes,
    trusted_anchor: str, epoch: int,
) -> dict:
    _keys(backup_key, manifest_key)
    if type(trusted_anchor) is not str or _DIGEST_RE.fullmatch(trusted_anchor) is None:
        raise RestoreCloneLabError("KIT_TRUSTED_ANCHOR_REQUIRED")
    payload = _read_catalog(
        vault, manifest_key, trusted_anchor, epoch, backup_key=backup_key
    )
    if payload["generation"] <= 0 or not payload["entries"]:
        raise RestoreCloneLabError("KIT_COMPLETED_VAULT_REQUIRED")
    return payload


def _read_sealed(
    path: Path, *, passphrase: bytes, expected_fingerprint: str,
) -> dict:
    if (type(expected_fingerprint) is not str
        or _DIGEST_RE.fullmatch(expected_fingerprint) is None):
        raise RestoreCloneLabError("KIT_EXTERNAL_WITNESS_REQUIRED")
    _passphrase(passphrase)
    if path.is_symlink() or not path.is_file():
        raise RestoreCloneLabError("KIT_STATE_INVALID")
    try:
        if not 0 < path.stat().st_size <= _MAX_KIT_SIZE:
            raise ValueError("kit size")
        encoded = path.read_bytes()
        if not hmac.compare_digest(
            sha256(encoded).hexdigest(), expected_fingerprint,
        ):
            raise RestoreCloneLabError("KIT_EXTERNAL_WITNESS_MISMATCH")
        envelope = json.loads(encoded)
        if type(envelope) is not dict or set(envelope) != {
            "version", "salt", "nonce", "ciphertext"
        } or envelope["version"] != 1:
            raise ValueError("envelope")
        salt = _unb64(envelope["salt"], _SALT_SIZE)
        nonce = _unb64(envelope["nonce"], _NONCE_SIZE)
        ciphertext = _unb64(envelope["ciphertext"])
        if not 16 <= len(ciphertext) <= 2048:
            raise ValueError("ciphertext size")
        try:
            plain = AESGCM(_derive(passphrase, salt)).decrypt(
                nonce, ciphertext, _AAD
            )
        except InvalidTag:
            raise RestoreCloneLabError("KIT_AUTHENTICATION_FAILED") from None
        payload = json.loads(plain)
        if type(payload) is not dict or set(payload) != {
            "version", "backup_key", "manifest_key", "anchor",
            "generation", "latest_epoch", "kit_identity",
        } or payload["version"] != 1:
            raise ValueError("contents")
        bk = _unb64(payload["backup_key"])
        mk = _unb64(payload["manifest_key"], 32)
        _keys(bk, mk)
        if (type(payload["anchor"]) is not str
            or _DIGEST_RE.fullmatch(payload["anchor"]) is None
            or type(payload["generation"]) is not int
            or payload["generation"] < 1
            or type(payload["latest_epoch"]) is not int
            or payload["latest_epoch"] < 0
            or type(payload["kit_identity"]) is not str
            or len(payload["kit_identity"]) != 32
            or any(c not in "0123456789abcdef" for c in payload["kit_identity"])):
            raise ValueError("contents")
        return {
            "backup_key": bk, "manifest_key": mk, "anchor": payload["anchor"],
            "generation": payload["generation"],
            "latest_epoch": payload["latest_epoch"],
            "kit_identity": payload["kit_identity"],
        }
    except RestoreCloneLabError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, OverflowError):
        raise RestoreCloneLabError("KIT_INVALID") from None


def _encrypt_payload(
    *, passphrase: bytes, backup_key: bytes, manifest_key: bytes,
    trusted_anchor: str, generation: int, latest_epoch: int,
    kit_identity: str,
) -> bytes:
    salt, nonce = os.urandom(_SALT_SIZE), os.urandom(_NONCE_SIZE)
    inner = {
        "version": 1, "backup_key": _b64(backup_key),
        "manifest_key": _b64(manifest_key), "anchor": trusted_anchor,
        "generation": generation, "latest_epoch": latest_epoch,
        "kit_identity": kit_identity,
    }
    ciphertext = AESGCM(_derive(passphrase, salt)).encrypt(
        nonce, _canonical(inner), _AAD,
    )
    encoded = _canonical({
        "version": 1, "salt": _b64(salt),
        "nonce": _b64(nonce), "ciphertext": _b64(ciphertext),
    })
    if len(encoded) > _MAX_KIT_SIZE:
        raise RestoreCloneLabError("KIT_INVALID")
    return encoded


def seal_queue_recovery_kit_lab(
    vault: str | Path, kit_directory: str | Path, *,
    backup_key: bytes, manifest_key: bytes, trusted_anchor: str,
    passphrase: bytes, now: datetime,
    previous_witness: str | None = None,
    previous_passphrase: bytes | None = None,
) -> LabKitReceipt:
    """Create or advance an encrypted kit AFTER a clean B2-C rotation.

    An update requires independently retained previous witness and old
    passphrase, matching immutable vault keys and strictly increasing
    catalog generation. An updated witness must also be stored externally;
    the filesystem operation is NOT atomic with its external custody.
    """
    _passphrase(passphrase)
    epoch = _now_epoch(now)
    root = _vault_folder(vault)
    folder = _kit_folder(kit_directory, root)
    catalog = _current_catalog(root, backup_key, manifest_key, trusted_anchor, epoch)
    path = folder / _KIT_FILE
    if path.is_symlink():
        raise RestoreCloneLabError("KIT_STATE_INVALID")
    creating = not path.exists()
    if creating:
        if previous_witness is not None or previous_passphrase is not None:
            raise RestoreCloneLabError("KIT_PREVIOUS_WITNESS_INVALID")
        identity = uuid4().hex
    else:
        if previous_witness is None or previous_passphrase is None:
            raise RestoreCloneLabError("KIT_PREVIOUS_WITNESS_REQUIRED")
        previous = _read_sealed(
            _kit_path(folder, exists=True), passphrase=previous_passphrase,
            expected_fingerprint=previous_witness,
        )
        if (previous["backup_key"] != backup_key
            or previous["manifest_key"] != manifest_key
            or catalog["generation"] <= previous["generation"]
            or catalog["latest_epoch"] < previous["latest_epoch"]
            or catalog["latest_epoch"] == previous["latest_epoch"]
            or previous["anchor"] == trusted_anchor):
            raise RestoreCloneLabError("KIT_GENERATION_OR_KEY_INVALID")
        identity = previous["kit_identity"]
    encoded = _encrypt_payload(
        passphrase=passphrase, backup_key=backup_key,
        manifest_key=manifest_key, trusted_anchor=trusted_anchor,
        generation=catalog["generation"], latest_epoch=catalog["latest_epoch"],
        kit_identity=identity,
    )
    fingerprint = sha256(encoded).hexdigest()
    stage = folder / f".lot08_3_b_lab_kit_stage_{uuid4().hex}.tmp"
    try:
        fd = os.open(str(stage), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        _before_kit_publish_lab()
        if creating:
            # Hard link is an atomic CREATE-ONLY; never overwrite a race.
            _kit_path(folder, exists=False)
            os.link(stage, path)
        else:
            _kit_path(folder, exists=True)
            if not hmac.compare_digest(sha256(path.read_bytes()).hexdigest(),
                                       previous_witness):
                raise RestoreCloneLabError("KIT_EXTERNAL_WITNESS_MISMATCH")
            os.replace(stage, path)
        return LabKitReceipt(
            witness_fingerprint=fingerprint, generation=catalog["generation"]
        )
    except FileExistsError:
        raise RestoreCloneLabError("KIT_STATE_INVALID") from None
    finally:
        stage.unlink(missing_ok=True)


def restore_queue_clone_from_kit_lab(
    vault: str | Path, kit_directory: str | Path,
    destination: str | Path, *, passphrase: bytes,
    expected_witness: str, slot: str, bucket: str, now: datetime,
) -> str:
    """Decrypt kit in process, authenticate latest catalog, create NEW clone."""
    epoch = _now_epoch(now)
    root = _vault_folder(vault)
    folder = _kit_folder(kit_directory, root)
    payload = _read_sealed(
        _kit_path(folder, exists=True), passphrase=passphrase,
        expected_fingerprint=expected_witness,
    )
    catalog = _current_catalog(
        root, payload["backup_key"], payload["manifest_key"],
        payload["anchor"], epoch,
    )
    if (catalog["generation"] != payload["generation"]
        or catalog["latest_epoch"] != payload["latest_epoch"]):
        raise RestoreCloneLabError("KIT_VAULT_GENERATION_MISMATCH")
    # B2-C delegates to B2-B: authenticated snapshot, 7D/4W window,
    # G3 visit/consumed QR anti-resurrection, and clone-only publication.
    return restore_queue_vault_clone_lab(
        root, destination, backup_key=payload["backup_key"],
        manifest_key=payload["manifest_key"],
        trusted_anchor=payload["anchor"],
        slot=slot, bucket=bucket, now=now,
    )
