from __future__ import annotations

import base64
import json
from typing import Any

from jwcrypto import jwe, jwk, jws

from relay.contract import JOSE_JWE_ALG, JOSE_JWE_ENC, JOSE_JWS_ALG

JWS_TYP = "application/dc-pc+jws"
JWE_TYP = "application/dc-pc+jwe"
JWE_CTY = JWS_TYP


def _json(value: dict[str, Any]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _protected_header(compact_token: str, expected_parts: int) -> dict[str, Any]:
    parts = compact_token.split(".")
    if len(parts) != expected_parts:
        raise ValueError("invalid compact JOSE serialization")
    segment = parts[0]
    padded = segment + "=" * (-len(segment) % 4)
    try:
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        header = json.loads(decoded.decode("utf-8"))
    except Exception as exc:
        raise ValueError("invalid JOSE protected header") from exc
    if not isinstance(header, dict):
        raise ValueError("invalid JOSE protected header")
    return header


def generate_p256_keypair(*, kid: str, use: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if use not in {"sig", "enc"}:
        raise ValueError("unsupported key use")
    private_key = jwk.JWK.generate(kty="EC", crv="P-256", kid=kid, use=use)
    public_key = jwk.JWK.from_json(private_key.export_public())
    return json.loads(private_key.export(private_key=True)), json.loads(public_key.export())


def sign_and_encrypt(
    payload: dict[str, Any],
    *,
    sender_signing_private_jwk: dict[str, Any],
    recipient_encryption_public_jwk: dict[str, Any],
    sender_signing_kid: str,
    recipient_encryption_kid: str,
) -> str:
    signing_key = jwk.JWK.from_json(_json(sender_signing_private_jwk))
    recipient_key = jwk.JWK.from_json(_json(recipient_encryption_public_jwk))

    signed = jws.JWS(_json(payload).encode("utf-8"))
    signed.allowed_algs = [JOSE_JWS_ALG]
    signed.add_signature(
        signing_key,
        protected=_json({
            "alg": JOSE_JWS_ALG,
            "kid": sender_signing_kid,
            "typ": JWS_TYP,
        }),
    )
    compact_jws = signed.serialize(compact=True)

    encrypted = jwe.JWE(
        compact_jws.encode("utf-8"),
        protected=_json({
            "alg": JOSE_JWE_ALG,
            "enc": JOSE_JWE_ENC,
            "kid": recipient_encryption_kid,
            "typ": JWE_TYP,
            "cty": JWE_CTY,
        }),
        algs=[JOSE_JWE_ALG, JOSE_JWE_ENC],
        recipient=recipient_key,
    )
    return encrypted.serialize(compact=True)


def decrypt_and_verify(
    compact_jwe: str,
    *,
    recipient_encryption_private_jwk: dict[str, Any],
    sender_signing_public_jwk: dict[str, Any],
    expected_sender_signing_kid: str,
    expected_recipient_encryption_kid: str,
) -> dict[str, Any]:
    jwe_header = _protected_header(compact_jwe, 5)
    expected_jwe = {
        "alg": JOSE_JWE_ALG,
        "enc": JOSE_JWE_ENC,
        "kid": expected_recipient_encryption_kid,
        "typ": JWE_TYP,
        "cty": JWE_CTY,
    }
    for key, value in expected_jwe.items():
        if jwe_header.get(key) != value:
            raise ValueError("unexpected JWE protected header")
    if set(jwe_header) != {*expected_jwe, "epk"}:
        raise ValueError("unexpected JWE protected header")
    epk = jwe_header.get("epk")
    if (
        not isinstance(epk, dict)
        or epk.get("kty") != "EC"
        or epk.get("crv") != "P-256"
        or not isinstance(epk.get("x"), str)
        or not isinstance(epk.get("y"), str)
        or "d" in epk
    ):
        raise ValueError("invalid ECDH ephemeral public key")

    recipient_key = jwk.JWK.from_json(_json(recipient_encryption_private_jwk))
    encrypted = jwe.JWE(algs=[JOSE_JWE_ALG, JOSE_JWE_ENC])
    encrypted.deserialize(compact_jwe, key=recipient_key)
    compact_jws = encrypted.payload.decode("utf-8")

    jws_header = _protected_header(compact_jws, 3)
    expected_jws = {
        "alg": JOSE_JWS_ALG,
        "kid": expected_sender_signing_kid,
        "typ": JWS_TYP,
    }
    if jws_header != expected_jws:
        raise ValueError("unexpected JWS protected header")

    sender_key = jwk.JWK.from_json(_json(sender_signing_public_jwk))
    signed = jws.JWS()
    signed.allowed_algs = [JOSE_JWS_ALG]
    signed.deserialize(compact_jws)
    signed.verify(sender_key, alg=JOSE_JWS_ALG)

    payload = json.loads(signed.payload.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("remote payload must be a JSON object")
    return payload
