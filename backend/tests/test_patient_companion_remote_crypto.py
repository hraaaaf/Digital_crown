from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jwcrypto import jwe, jwk
from jwcrypto.common import json_encode

from backend.services.patient_companion_remote_crypto import (
    JWE_CTY,
    JWE_TYP,
    decrypt_and_verify,
    generate_p256_keypair,
    sign_and_encrypt,
)
from relay.contract import JOSE_JWE_ALG, JOSE_JWE_ENC


def _inner_payload():
    now = datetime.now(timezone.utc)
    return {
        "protocol_version": "dc-pc-remote-v1",
        "message_id": str(uuid.uuid4()),
        "access_id": str(uuid.uuid4()),
        "sent_at": now.isoformat(),
        "expires_at": (now + timedelta(minutes=10)).isoformat(),
        "idempotency_key": str(uuid.uuid4()),
        "operation": "appointment.request",
        "payload": {"slot": "opaque-domain-value"},
    }


def test_sign_then_encrypt_roundtrip_and_header_minimization():
    sender_kid = str(uuid.uuid4())
    recipient_kid = str(uuid.uuid4())
    sender_private, sender_public = generate_p256_keypair(kid=sender_kid, use="sig")
    recipient_private, recipient_public = generate_p256_keypair(kid=recipient_kid, use="enc")
    payload = _inner_payload()

    token = sign_and_encrypt(
        payload,
        sender_signing_private_jwk=sender_private,
        recipient_encryption_public_jwk=recipient_public,
        sender_signing_kid=sender_kid,
        recipient_encryption_kid=recipient_kid,
    )

    assert payload["operation"] not in token
    assert payload["access_id"] not in token
    assert len(token.split(".")) == 5

    decoded = decrypt_and_verify(
        token,
        recipient_encryption_private_jwk=recipient_private,
        sender_signing_public_jwk=sender_public,
        expected_sender_signing_kid=sender_kid,
        expected_recipient_encryption_kid=recipient_kid,
    )
    assert decoded == payload


def test_wrong_recipient_key_cannot_decrypt():
    sender_kid = str(uuid.uuid4())
    recipient_kid = str(uuid.uuid4())
    sender_private, sender_public = generate_p256_keypair(kid=sender_kid, use="sig")
    _recipient_private, recipient_public = generate_p256_keypair(kid=recipient_kid, use="enc")
    wrong_private, _wrong_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="enc")

    token = sign_and_encrypt(
        _inner_payload(),
        sender_signing_private_jwk=sender_private,
        recipient_encryption_public_jwk=recipient_public,
        sender_signing_kid=sender_kid,
        recipient_encryption_kid=recipient_kid,
    )

    with pytest.raises(Exception):
        decrypt_and_verify(
            token,
            recipient_encryption_private_jwk=wrong_private,
            sender_signing_public_jwk=sender_public,
            expected_sender_signing_kid=sender_kid,
            expected_recipient_encryption_kid=recipient_kid,
        )


def test_wrong_sender_key_cannot_verify():
    sender_kid = str(uuid.uuid4())
    recipient_kid = str(uuid.uuid4())
    sender_private, _sender_public = generate_p256_keypair(kid=sender_kid, use="sig")
    _wrong_private, wrong_public = generate_p256_keypair(kid=str(uuid.uuid4()), use="sig")
    recipient_private, recipient_public = generate_p256_keypair(kid=recipient_kid, use="enc")

    token = sign_and_encrypt(
        _inner_payload(),
        sender_signing_private_jwk=sender_private,
        recipient_encryption_public_jwk=recipient_public,
        sender_signing_kid=sender_kid,
        recipient_encryption_kid=recipient_kid,
    )

    with pytest.raises(Exception):
        decrypt_and_verify(
            token,
            recipient_encryption_private_jwk=recipient_private,
            sender_signing_public_jwk=wrong_public,
            expected_sender_signing_kid=sender_kid,
            expected_recipient_encryption_kid=recipient_kid,
        )


def test_algorithm_confusion_is_rejected_before_domain_payload():
    recipient_kid = str(uuid.uuid4())
    recipient_private, recipient_public = generate_p256_keypair(kid=recipient_kid, use="enc")

    public_key = jwk.JWK.from_json(json.dumps(recipient_public))
    alternate = jwe.JWE(
        b"not-a-valid-signed-payload",
        protected=json_encode({
            "alg": JOSE_JWE_ALG,
            "enc": "A128GCM",
            "kid": recipient_kid,
            "typ": JWE_TYP,
            "cty": JWE_CTY,
        }),
        recipient=public_key,
    ).serialize(compact=True)

    with pytest.raises(ValueError, match="unexpected JWE protected header"):
        decrypt_and_verify(
            alternate,
            recipient_encryption_private_jwk=recipient_private,
            sender_signing_public_jwk=recipient_public,
            expected_sender_signing_kid="irrelevant",
            expected_recipient_encryption_kid=recipient_kid,
        )
