from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RELAY_PROTOCOL = "dc-relay-v1"
RELAY_MAX_BLOB_BYTES = 256 * 1024
RELAY_MAX_TTL_SECONDS = 7 * 24 * 60 * 60
RELAY_MIN_TTL_SECONDS = 60
RELAY_CAPABILITY_BYTES = 32

JOSE_JWS_ALG = "ES256"
JOSE_JWE_ALG = "ECDH-ES+A256KW"
JOSE_JWE_ENC = "A256GCM"
JOSE_ALLOWED_JWS_ALGS = frozenset({JOSE_JWS_ALG})
JOSE_ALLOWED_JWE_ALGS = frozenset({JOSE_JWE_ALG})
JOSE_ALLOWED_JWE_ENCS = frozenset({JOSE_JWE_ENC})

RelayPrivilege = Literal["read", "write"]


class RelayEnvelopeCreate(BaseModel):
    """Relay-visible request. Clinical routing metadata is deliberately impossible here."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    envelope_id: uuid.UUID
    blob: str = Field(min_length=16)
    ttl_seconds: int = Field(ge=RELAY_MIN_TTL_SECONDS, le=RELAY_MAX_TTL_SECONDS)

    @field_validator("blob")
    @classmethod
    def enforce_blob_limit(cls, value: str) -> str:
        if len(value.encode("utf-8")) > RELAY_MAX_BLOB_BYTES:
            raise ValueError("relay blob exceeds v1 size limit")
        return value


class RelayEnvelopeRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    envelope_id: uuid.UUID
    blob: str
    created_at: datetime
    expires_at: datetime


class RelayMailboxCredential(BaseModel):
    """Provisioning response only. Raw capabilities must never be persisted by relay."""

    model_config = ConfigDict(extra="forbid")

    mailbox_id: uuid.UUID
    read_capability: str = Field(min_length=43, max_length=64)
    write_capability: str = Field(min_length=43, max_length=64)


class RelayInnerMessage(BaseModel):
    """Signed application object before JWE encryption; never relay-visible."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: Literal["dc-pc-remote-v1"] = "dc-pc-remote-v1"
    message_id: uuid.UUID
    access_id: uuid.UUID
    sent_at: datetime
    expires_at: datetime
    idempotency_key: uuid.UUID
    operation: str = Field(min_length=1, max_length=64)
    payload: dict

    @field_validator("sent_at", "expires_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("remote message timestamps must be timezone-aware")
        return value

    def assert_fresh(self, *, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        if now > self.expires_at:
            raise ValueError("remote message expired")
        if self.expires_at <= self.sent_at:
            raise ValueError("remote message expiry must be after sent_at")


def new_mailbox_id() -> uuid.UUID:
    return uuid.uuid4()


def new_relay_capability() -> str:
    # token_urlsafe(32) provides 256 bits of random input.
    return secrets.token_urlsafe(RELAY_CAPABILITY_BYTES)


def capability_hash(raw_capability: str) -> str:
    return hashlib.sha256(raw_capability.encode("utf-8")).hexdigest()


def capability_matches(raw_capability: str, stored_hash: str) -> bool:
    return hmac.compare_digest(capability_hash(raw_capability), stored_hash)
