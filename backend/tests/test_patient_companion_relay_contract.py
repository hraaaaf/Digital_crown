from datetime import datetime, timedelta, timezone
import uuid

import pytest
from pydantic import ValidationError

from relay.contract import (
    JOSE_ALLOWED_JWE_ALGS,
    JOSE_ALLOWED_JWE_ENCS,
    JOSE_ALLOWED_JWS_ALGS,
    RELAY_MAX_BLOB_BYTES,
    RELAY_MAX_TTL_SECONDS,
    RelayEnvelopeCreate,
    RelayInnerMessage,
    capability_hash,
    capability_matches,
    new_relay_capability,
)


def test_relay_envelope_has_no_clinical_routing_metadata():
    envelope = RelayEnvelopeCreate(
        envelope_id=uuid.uuid4(),
        blob="x" * 32,
        ttl_seconds=60,
    )
    dumped = envelope.model_dump()
    assert set(dumped) == {"envelope_id", "blob", "ttl_seconds"}
    for forbidden in ("patient_id", "employer_id", "tenant_id", "access_id", "resource_id", "operation"):
        assert forbidden not in dumped


@pytest.mark.parametrize("field", ["patient_id", "employer_id", "tenant_id", "access_id", "resource_id", "operation"])
def test_relay_envelope_rejects_clinical_metadata(field):
    payload = {
        "envelope_id": uuid.uuid4(),
        "blob": "x" * 32,
        "ttl_seconds": 60,
        field: "leak",
    }
    with pytest.raises(ValidationError):
        RelayEnvelopeCreate(**payload)


def test_relay_envelope_bounds_size_and_retention():
    with pytest.raises(ValidationError):
        RelayEnvelopeCreate(
            envelope_id=uuid.uuid4(),
            blob="x" * (RELAY_MAX_BLOB_BYTES + 1),
            ttl_seconds=60,
        )
    with pytest.raises(ValidationError):
        RelayEnvelopeCreate(
            envelope_id=uuid.uuid4(),
            blob="x" * 32,
            ttl_seconds=RELAY_MAX_TTL_SECONDS + 1,
        )


def test_relay_capabilities_are_random_hashed_and_constant_time_comparable():
    raw = new_relay_capability()
    other = new_relay_capability()
    assert raw != other
    digest = capability_hash(raw)
    assert len(digest) == 64
    assert raw not in digest
    assert capability_matches(raw, digest)
    assert not capability_matches(other, digest)


def test_crypto_algorithm_allowlists_are_fixed():
    assert JOSE_ALLOWED_JWS_ALGS == {"ES256"}
    assert JOSE_ALLOWED_JWE_ALGS == {"ECDH-ES+A256KW"}
    assert JOSE_ALLOWED_JWE_ENCS == {"A256GCM"}


def test_inner_message_rejects_expired_and_naive_time():
    now = datetime.now(timezone.utc)
    msg = RelayInnerMessage(
        message_id=uuid.uuid4(),
        access_id=uuid.uuid4(),
        sent_at=now - timedelta(minutes=20),
        expires_at=now - timedelta(minutes=5),
        idempotency_key=uuid.uuid4(),
        operation="appointment.request",
        payload={"opaque_domain_payload": True},
    )
    with pytest.raises(ValueError, match="expired"):
        msg.assert_fresh(now=now)

    with pytest.raises(ValidationError):
        RelayInnerMessage(
            message_id=uuid.uuid4(),
            access_id=uuid.uuid4(),
            sent_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            idempotency_key=uuid.uuid4(),
            operation="appointment.request",
            payload={},
        )
