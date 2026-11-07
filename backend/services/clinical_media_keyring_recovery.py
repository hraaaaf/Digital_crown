"""F5B-D: offline encrypted keyring recovery envelope.

No automatic backup, storage, network, or password logging. Callers must keep
recovery passwords outside the application and must independently protect backups.
"""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_MAGIC = b"DC06REC1"
_AAD = b"digital-crown-dcm2-keyring-recovery-v1"
_MAX_PLAIN = 16384
_MAX_ENVELOPE = 16464
_SCRYPT_N = 1 << 15
_SCRYPT_R = 8
_SCRYPT_P = 1


class KeyringRecoveryDenied(ValueError):
    pass


def _password(password: bytes) -> bytes:
    if not isinstance(password, bytes) or not 16 <= len(password) <= 1024:
        raise KeyringRecoveryDenied("RECOVERY_PASSWORD_INVALID")
    return password


def _key(password: bytes, salt: bytes) -> bytes:
    try:
        return hashlib.scrypt(
            _password(password), salt=salt, n=_SCRYPT_N,
            r=_SCRYPT_R, p=_SCRYPT_P, dklen=32, maxmem=64 * 1024 * 1024,
        )
    except (ValueError, MemoryError) as exc:
        raise KeyringRecoveryDenied("RECOVERY_DERIVATION_FAILED") from exc


def _canonical(data: Any) -> bytes:
    if not isinstance(data, dict) or set(data) != {
        "active_media_id", "active_locator_id", "media_keys", "locator_keys"
    }:
        raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID")
    for purpose, active in (("media_keys", "active_media_id"),
                            ("locator_keys", "active_locator_id")):
        keys = data[purpose]
        if not isinstance(keys, dict) or not 1 <= len(keys) <= 64:
            raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID")
        if data[active] not in keys:
            raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID")
        for key_id, value in keys.items():
            if (not isinstance(key_id, str) or not 1 <= len(key_id) <= 32
                    or not key_id[0].islower()
                    or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789_-"
                           for ch in key_id)
                    or not isinstance(value, str) or len(value) != 64):
                raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID")
            try:
                bytes.fromhex(value)
            except ValueError as exc:
                raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID") from exc
    if set(data["media_keys"].values()) & set(data["locator_keys"].values()):
        raise KeyringRecoveryDenied("RECOVERY_KEY_PURPOSE_REUSE_DENIED")
    try:
        raw = json.dumps(data, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=True, allow_nan=False).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID") from exc
    if len(raw) > _MAX_PLAIN:
        raise KeyringRecoveryDenied("RECOVERY_KEYRING_TOO_LARGE")
    return raw


def seal_keyring(data: dict, password: bytes) -> bytes:
    """Explicit offline backup: authenticated AES-256-GCM, scrypt, random salt/nonce."""
    raw = _canonical(data)
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _key(password, salt)
    envelope = _MAGIC + salt + nonce + AESGCM(key).encrypt(nonce, raw, _AAD)
    if len(envelope) > _MAX_ENVELOPE:
        raise KeyringRecoveryDenied("RECOVERY_ENVELOPE_TOO_LARGE")
    return envelope


def open_keyring(envelope: bytes, password: bytes) -> dict:
    """Authenticate before JSON parse; reject malformed/wrong-password/tampered data."""
    if (not isinstance(envelope, bytes)
            or not 52 <= len(envelope) <= _MAX_ENVELOPE
            or not envelope.startswith(_MAGIC)):
        raise KeyringRecoveryDenied("RECOVERY_ENVELOPE_INVALID")
    salt = envelope[len(_MAGIC):len(_MAGIC) + 16]
    nonce = envelope[len(_MAGIC) + 16:len(_MAGIC) + 28]
    ciphertext = envelope[len(_MAGIC) + 28:]
    try:
        raw = AESGCM(_key(password, salt)).decrypt(nonce, ciphertext, _AAD)
    except InvalidTag as exc:
        raise KeyringRecoveryDenied("RECOVERY_AUTHENTICATION_FAILED") from exc
    if len(raw) > _MAX_PLAIN:
        raise KeyringRecoveryDenied("RECOVERY_KEYRING_TOO_LARGE")
    try:
        data = json.loads(raw.decode("ascii"))
    except (UnicodeError, ValueError) as exc:
        raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID") from exc
    if _canonical(data) != raw:
        raise KeyringRecoveryDenied("RECOVERY_KEYRING_INVALID")
    return data
