"""LOT06-I synthetic versioned AES-GCM spool envelope.

NO integration with active HotFolder/CLI, no disk writes, migration or patient data.
All failures are fixed codes and never disclose scope, key or media bytes.
"""
from __future__ import annotations

import hashlib
import re
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC_V1 = b"DC6A"
MAGIC_V2 = b"DC6B"
MAX_CLEAR_BYTES = 50 * 1024 * 1024
V1_OVERHEAD = 4 + 12 + 16
V2_OVERHEAD = 4 + 16 + 12 + 16
_SCOPE = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_KEY_ID = re.compile(r"[0-9a-f]{32}\Z")


class SpoolCodecError(RuntimeError):
    """Opaque fixed error codes, safe for synthetic diagnostics."""


def _scope(cabinet: str, workstation: str, identity: str, digest: str) -> None:
    if (type(cabinet) is not str or type(workstation) is not str
            or not _SCOPE.fullmatch(cabinet)
            or not _SCOPE.fullmatch(workstation)
            or type(identity) is not str or not _SHA.fullmatch(identity)
            or type(digest) is not str or not _SHA.fullmatch(digest)):
        raise SpoolCodecError("INVALID_ENVELOPE_SCOPE")


def _key(raw: bytes) -> bytes:
    if type(raw) is not bytes or len(raw) != 32:
        raise SpoolCodecError("INVALID_AES256_KEY")
    return raw


def _key_id(value: str) -> str:
    if type(value) is not str or not _KEY_ID.fullmatch(value):
        raise SpoolCodecError("INVALID_KEY_ID")
    return value


def _keyring(keys: dict) -> None:
    if type(keys) is not dict or not keys:
        raise SpoolCodecError("INVALID_KEYRING")
    for key_id, material in keys.items():
        _key_id(key_id)
        _key(material)
    if len(set(keys.values())) != len(keys):
        raise SpoolCodecError("KEY_MATERIAL_REUSED_ACROSS_IDS")


def _v2_aad(cabinet: str, workstation: str, identity: str,
            header: bytes) -> bytes:
    return (b"DC06I|" + cabinet.encode("ascii") + b"|" +
            workstation.encode("ascii") + b"|" +
            identity.encode("ascii") + b"|" + header)


def _check_digest(content: bytes, expected: str) -> None:
    if hashlib.sha256(content).hexdigest() != expected:
        raise SpoolCodecError("SPOOL_DIGEST_MISMATCH")


def encode_v2(clear: bytes, *, cabinet: str, workstation: str,
              identity: str, digest: str, key_id: str, keys: dict) -> bytes:
    """New versioned format, in-memory only. Never rewrites a v1 object."""
    _scope(cabinet, workstation, identity, digest)
    _key_id(key_id)
    _keyring(keys)
    if key_id not in keys:
        raise SpoolCodecError("KEY_ID_UNAVAILABLE")
    if type(clear) is not bytes or not 0 < len(clear) <= MAX_CLEAR_BYTES:
        raise SpoolCodecError("SPOOL_CLEAR_SIZE_INVALID")
    _check_digest(clear, digest)
    header = MAGIC_V2 + bytes.fromhex(key_id)
    nonce = secrets.token_bytes(12)
    return (header + nonce + AESGCM(keys[key_id]).encrypt(
        nonce, clear, _v2_aad(cabinet, workstation, identity, header)
    ))


def decode_v2(blob: bytes, *, cabinet: str, workstation: str,
              identity: str, digest: str, keys: dict) -> bytes:
    """Strict v2 parser: no fallback to v1, no guessing at keys."""
    _scope(cabinet, workstation, identity, digest)
    if type(blob) is not bytes or not blob.startswith(MAGIC_V2):
        raise SpoolCodecError("V2_ENVELOPE_REQUIRED")
    if not V2_OVERHEAD < len(blob) <= MAX_CLEAR_BYTES + V2_OVERHEAD:
        raise SpoolCodecError("SPOOL_ENVELOPE_SIZE_INVALID")
    _keyring(keys)
    header = blob[:20]
    key_id = header[4:].hex()
    if key_id not in keys:
        raise SpoolCodecError("KEY_ID_UNAVAILABLE")
    nonce = blob[20:32]
    try:
        clear = AESGCM(keys[key_id]).decrypt(
            nonce, blob[32:], _v2_aad(cabinet, workstation, identity, header)
        )
    except Exception:
        raise SpoolCodecError("SPOOL_AUTHENTICATION_FAILED") from None
    _check_digest(clear, digest)
    return clear


def decode_legacy_v1(blob: bytes, *, cabinet: str, workstation: str,
                     identity: str, digest: str, legacy_key: bytes) -> bytes:
    """Only explicit old key + exact DC06A historical AAD are acceptable."""
    _scope(cabinet, workstation, identity, digest)
    _key(legacy_key)
    if type(blob) is not bytes or not blob.startswith(MAGIC_V1):
        raise SpoolCodecError("V1_ENVELOPE_REQUIRED")
    if not V1_OVERHEAD < len(blob) <= MAX_CLEAR_BYTES + V1_OVERHEAD:
        raise SpoolCodecError("SPOOL_ENVELOPE_SIZE_INVALID")
    aad = ("DC06A|" + cabinet + "|" + workstation + "|" + identity).encode("ascii")
    try:
        clear = AESGCM(legacy_key).decrypt(blob[4:16], blob[16:], aad)
    except Exception:
        raise SpoolCodecError("SPOOL_AUTHENTICATION_FAILED") from None
    _check_digest(clear, digest)
    return clear


def rewrap_legacy_v1(blob: bytes, *, cabinet: str, workstation: str,
                     identity: str, digest: str, legacy_key: bytes,
                     target_key_id: str, keys: dict) -> bytes:
    """Pure copy-on-write *candidate bytes*. No persistence or key destruction.

    The caller must later design an atomic journaled storage protocol,
    verified old-key retention and rollback before any real migration.
    """
    clear = decode_legacy_v1(
        blob, cabinet=cabinet, workstation=workstation, identity=identity,
        digest=digest, legacy_key=legacy_key
    )
    _key_id(target_key_id)
    _keyring(keys)
    if target_key_id not in keys:
        raise SpoolCodecError("KEY_ID_UNAVAILABLE")
    if keys[target_key_id] == legacy_key:
        raise SpoolCodecError("ROTATION_TARGET_KEY_REUSED")
    candidate = encode_v2(
        clear, cabinet=cabinet, workstation=workstation, identity=identity,
        digest=digest, key_id=target_key_id, keys=keys
    )
    if decode_v2(
        candidate, cabinet=cabinet, workstation=workstation,
        identity=identity, digest=digest, keys=keys
    ) != clear:
        raise SpoolCodecError("REWRAP_VERIFICATION_FAILED")
    return candidate
