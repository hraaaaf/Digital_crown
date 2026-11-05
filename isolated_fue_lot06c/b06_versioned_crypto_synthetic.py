"""B06-4D-F1: isolated synthetic-only versioned media crypto contract.

Not wired to product storage, schema, migration, or real cabinet runtime.
"""
from __future__ import annotations

import hashlib
import hmac
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


class SyntheticCryptoDenied(RuntimeError):
    """Fail closed without leaking keys or ciphertext."""


def _valid_id(value: str) -> str:
    if not isinstance(value, str) or not _KEY_ID.fullmatch(value):
        raise SyntheticCryptoDenied("INVALID_KEY_ID")
    return value


def _key(keys: Mapping[str, bytes], key_id: str) -> bytes:
    _valid_id(key_id)
    value = keys.get(key_id)
    if not isinstance(value, bytes) or len(value) != 32:
        raise SyntheticCryptoDenied("KEY_UNAVAILABLE")
    return value


@dataclass(frozen=True)
class SyntheticKeyring:
    media_keys: Mapping[str, bytes]
    locator_keys: Mapping[str, bytes]

    def encrypt(self, *, tenant: int, digest: str, plaintext: bytes, media_key_id: str) -> bytes:
        if not isinstance(plaintext, bytes) or not plaintext:
            raise SyntheticCryptoDenied("INVALID_MEDIA")
        _check_digest(digest)
        if hashlib.sha256(plaintext).hexdigest() != digest:
            raise SyntheticCryptoDenied("DIGEST_MISMATCH")
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
            raise SyntheticCryptoDenied("INVALID_ENVELOPE")
        if envelope[:4] != _MAGIC:
            raise SyntheticCryptoDenied("INVALID_ENVELOPE")
        n = envelope[4]
        if n < 1 or n > 32 or len(envelope) < 5 + n + _NONCE_SIZE + 16:
            raise SyntheticCryptoDenied("INVALID_ENVELOPE")
        header = envelope[:5 + n]
        try:
            key_id = envelope[5:5 + n].decode("ascii")
        except UnicodeDecodeError as exc:
            raise SyntheticCryptoDenied("INVALID_ENVELOPE") from exc
        key = _key(self.media_keys, key_id)
        nonce = envelope[5 + n:5 + n + _NONCE_SIZE]
        ciphertext = envelope[5 + n + _NONCE_SIZE:]
        try:
            plain = AESGCM(key).decrypt(nonce, ciphertext, _aad(tenant, digest, header))
        except (InvalidTag, ValueError) as exc:
            raise SyntheticCryptoDenied("AUTHENTICATION_FAILED") from exc
        if hashlib.sha256(plain).hexdigest() != digest:
            raise SyntheticCryptoDenied("DIGEST_MISMATCH")
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
        raise SyntheticCryptoDenied("INVALID_TENANT")
    return tenant


def _check_digest(digest: str) -> None:
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise SyntheticCryptoDenied("INVALID_DIGEST")


def _aad(tenant: int, digest: str, header: bytes) -> bytes:
    return _PURPOSE + b"\0" + str(_tenant(tenant)).encode("ascii") + b"\0" + digest.encode("ascii") + b"\0" + header
