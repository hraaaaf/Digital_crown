"""B06-4D-F2: versioned media crypto primitive for opt-in product storage.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import stat
from pathlib import Path
import os
import re
from dataclasses import dataclass
from typing import Mapping

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_MAGIC = b"DCM2"
_NONCE_SIZE = 12
_KEY_ID = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z", re.ASCII)
_PURPOSE = b"dc06-media-v2"


class MediaCryptoV2Denied(RuntimeError):
    """Fail closed without leaking keys or ciphertext."""


def _valid_id(value: str) -> str:
    if not isinstance(value, str) or not _KEY_ID.fullmatch(value):
        raise MediaCryptoV2Denied("INVALID_KEY_ID")
    return value


def _key(keys: Mapping[str, bytes], key_id: str) -> bytes:
    _valid_id(key_id)
    value = keys.get(key_id)
    if not isinstance(value, bytes) or len(value) != 32:
        raise MediaCryptoV2Denied("KEY_UNAVAILABLE")
    return value


@dataclass(frozen=True)
class MediaKeyringV2:
    media_keys: Mapping[str, bytes]
    locator_keys: Mapping[str, bytes]

    def encrypt(self, *, tenant: int, digest: str, plaintext: bytes, media_key_id: str) -> bytes:
        if not isinstance(plaintext, bytes) or not plaintext:
            raise MediaCryptoV2Denied("INVALID_MEDIA")
        _check_digest(digest)
        if hashlib.sha256(plaintext).hexdigest() != digest:
            raise MediaCryptoV2Denied("DIGEST_MISMATCH")
        key = _key(self.media_keys, media_key_id)
        key_id = media_key_id.encode("ascii")
        header = _MAGIC + bytes([len(key_id)]) + key_id
        nonce = os.urandom(_NONCE_SIZE)
        return header + nonce + AESGCM(key).encrypt(
            nonce, plaintext, _aad(tenant, digest, header)
        )

    def decrypt(self, *, tenant: int, digest: str, envelope: bytes) -> bytes:
        _check_digest(digest)
        if not isinstance(envelope, bytes) or len(envelope) < 5 + 1 + _NONCE_SIZE + 16:
            raise MediaCryptoV2Denied("INVALID_ENVELOPE")
        if envelope[:4] != _MAGIC:
            raise MediaCryptoV2Denied("INVALID_ENVELOPE")
        n = envelope[4]
        if n < 1 or n > 32 or len(envelope) < 5 + n + _NONCE_SIZE + 16:
            raise MediaCryptoV2Denied("INVALID_ENVELOPE")
        header = envelope[:5 + n]
        try:
            key_id = envelope[5:5 + n].decode("ascii")
        except UnicodeDecodeError as exc:
            raise MediaCryptoV2Denied("INVALID_ENVELOPE") from exc
        key = _key(self.media_keys, key_id)
        nonce = envelope[5 + n:5 + n + _NONCE_SIZE]
        ciphertext = envelope[5 + n + _NONCE_SIZE:]
        try:
            plain = AESGCM(key).decrypt(nonce, ciphertext, _aad(tenant, digest, header))
        except (InvalidTag, ValueError) as exc:
            raise MediaCryptoV2Denied("AUTHENTICATION_FAILED") from exc
        if hashlib.sha256(plain).hexdigest() != digest:
            raise MediaCryptoV2Denied("DIGEST_MISMATCH")
        return plain

    def locator(self, *, tenant: int, digest: str, locator_key_id: str) -> str:
        _check_digest(digest)
        key = _key(self.locator_keys, locator_key_id)
        return hmac.new(
            key, b"dc06-locator-v2\0" + str(_tenant(tenant)).encode("ascii") +
            b"\0" + digest.encode("ascii"), hashlib.sha256
        ).hexdigest()


def _tenant(tenant: int) -> int:
    if type(tenant) is not int or tenant <= 0:
        raise MediaCryptoV2Denied("INVALID_TENANT")
    return tenant


def _check_digest(digest: str) -> None:
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise MediaCryptoV2Denied("INVALID_DIGEST")


def _aad(tenant: int, digest: str, header: bytes) -> bytes:
    return _PURPOSE + b"\0" + str(_tenant(tenant)).encode("ascii") + b"\0" + digest.encode("ascii") + b"\0" + header

def _parse_key_map(parsed: object) -> dict[str, bytes]:
    if not isinstance(parsed, dict) or len(parsed) > 64:
        raise MediaCryptoV2Denied("INVALID_KEY_REGISTRY")
    result: dict[str, bytes] = {}
    for key_id, value in parsed.items():
        _valid_id(key_id)
        if not isinstance(value, str) or len(value) != 64:
            raise MediaCryptoV2Denied("INVALID_KEY_REGISTRY")
        try:
            result[key_id] = bytes.fromhex(value)
        except ValueError as exc:
            raise MediaCryptoV2Denied("INVALID_KEY_REGISTRY") from exc
    return result


def _retained_keys(env_name: str) -> dict[str, bytes]:
    """Explicit JSON map of historical key IDs to 64-char hex keys."""
    raw = os.environ.get(env_name, "{}")
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise MediaCryptoV2Denied("INVALID_KEY_REGISTRY") from exc
    return _parse_key_map(parsed)

def _private_keyring_file() -> dict | None:
    """POSIX-only local private keyring; no symlink or group/other access."""
    filename = os.environ.get("DC_MEDIA_V2_KEYRING_FILE")
    if not filename:
        return None
    if os.name != "posix":
        raise MediaCryptoV2Denied("KEYRING_FILE_PLATFORM_UNSUPPORTED")
    path = Path(filename)
    try:
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
            raise MediaCryptoV2Denied("INSECURE_KEYRING_FILE")
        if metadata.st_uid != os.geteuid():
            raise MediaCryptoV2Denied("INSECURE_KEYRING_OWNER")
        if metadata.st_size > 16384:
            raise MediaCryptoV2Denied("KEYRING_FILE_TOO_LARGE")
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, UnicodeError, ValueError) as exc:
        raise MediaCryptoV2Denied("INVALID_KEYRING_FILE") from exc
    if not isinstance(data, dict):
        raise MediaCryptoV2Denied("INVALID_KEYRING_FILE")
    return data


def configured_keyring() -> tuple[MediaKeyringV2, str, str]:
    """Opt-in key IDs and hex keys; no default, fallback, or secret logging."""
    file_data = _private_keyring_file()
    if file_data is not None:
        if any(os.environ.get(name) for name in (
            "DC_MEDIA_V2_ACTIVE_KEY_ID", "DC_MEDIA_V2_LOCATOR_KEY_ID",
            "DC_MEDIA_V2_MEDIA_KEY_HEX", "DC_MEDIA_V2_LOCATOR_KEY_HEX",
            "DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON", "DC_MEDIA_V2_RETAINED_LOCATOR_KEYS_JSON",
        )):
            raise MediaCryptoV2Denied("MIXED_KEYRING_SOURCES")
        required = {"active_media_id", "active_locator_id", "media_keys", "locator_keys"}
        if set(file_data) != required or not all(isinstance(file_data[k], dict) for k in ("media_keys", "locator_keys")):
            raise MediaCryptoV2Denied("INVALID_KEYRING_FILE")
        media_id = _valid_id(file_data["active_media_id"])
        locator_id = _valid_id(file_data["active_locator_id"])
        media_keys = _parse_key_map(file_data["media_keys"])
        locator_keys = _parse_key_map(file_data["locator_keys"])
        _key(media_keys, media_id)
        _key(locator_keys, locator_id)
        if any(hmac.compare_digest(m, l) for m in media_keys.values() for l in locator_keys.values()):
            raise MediaCryptoV2Denied("KEY_PURPOSE_REUSE_DENIED")
        return MediaKeyringV2(media_keys, locator_keys), media_id, locator_id
    media_id = _valid_id(os.environ.get("DC_MEDIA_V2_ACTIVE_KEY_ID", ""))
    locator_id = _valid_id(os.environ.get("DC_MEDIA_V2_LOCATOR_KEY_ID", ""))
    media_hex = os.environ.get("DC_MEDIA_V2_MEDIA_KEY_HEX", "")
    locator_hex = os.environ.get("DC_MEDIA_V2_LOCATOR_KEY_HEX", "")
    if len(media_hex) != 64 or len(locator_hex) != 64:
        raise MediaCryptoV2Denied("KEY_UNAVAILABLE")
    try:
        media_key, locator_key = bytes.fromhex(media_hex), bytes.fromhex(locator_hex)
    except ValueError as exc:
        raise MediaCryptoV2Denied("KEY_UNAVAILABLE") from exc
    media_keys = _retained_keys("DC_MEDIA_V2_RETAINED_MEDIA_KEYS_JSON")
    locator_keys = _retained_keys("DC_MEDIA_V2_RETAINED_LOCATOR_KEYS_JSON")
    if media_id in media_keys and not hmac.compare_digest(media_keys[media_id], media_key):
        raise MediaCryptoV2Denied("ACTIVE_KEY_CONFLICT")
    if locator_id in locator_keys and not hmac.compare_digest(locator_keys[locator_id], locator_key):
        raise MediaCryptoV2Denied("ACTIVE_KEY_CONFLICT")
    media_keys[media_id] = media_key
    locator_keys[locator_id] = locator_key
    if any(hmac.compare_digest(m, l) for m in media_keys.values() for l in locator_keys.values()):
        raise MediaCryptoV2Denied("KEY_PURPOSE_REUSE_DENIED")
    if hmac.compare_digest(media_key, locator_key):
        raise MediaCryptoV2Denied("KEY_PURPOSE_REUSE_DENIED")
    return MediaKeyringV2(
        media_keys=media_keys,
        locator_keys=locator_keys,
    ), media_id, locator_id
