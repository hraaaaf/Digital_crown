"""FUE-G05.7A: verifier-only adversarial tests with ephemeral synthetic keys.

This suite cannot certify Windows installer, issuer independence, authenticated
IPC, durable replay after a real crash/DB rollback or clinical import.
"""
import base64
from dataclasses import replace
import hashlib
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from backend.services.legacy_migration_trust_root_v15 import (
    ExpectedSyntheticContext, ProvisionedVerifier, SyntheticAuthorityDenied,
    verify_synthetic_noop_ticket,
)


_AUDIENCE = "digital-crown:lot05:synthetic-noop:v1"
_DOMAIN = b"DIGITAL-CROWN-LOT05-SYNTHETIC-NOOP-V1\x00"


def sha(char):
    return char * 64


def canon(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


class FakeLedger:
    """Only a disposable test double, NOT an anti-rollback product ledger."""

    def __init__(self):
        self.seen = set()

    def consume_once(self, namespace, nonce):
        token = (namespace, nonce)
        if token in self.seen:
            return False
        self.seen.add(token)
        return True


def make_fixture():
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                               format=serialization.PublicFormat.Raw)
    pin = ProvisionedVerifier(public, hashlib.sha256(public).hexdigest(), "fixture-key-1",
                               "S-1-5-80-100200300", sha("a"), 1)
    context = ExpectedSyntheticContext("fixture-tenant-a", sha("1"), sha("2"),
                                       sha("3"), sha("4"), sha("5"), sha("6"))
    body = dict(version=1, audience=_AUDIENCE, operation="SYNTHETIC_NOOP",
                tenant_id=context.tenant_id, source_sha256=context.source_sha256,
                target_sha256=context.target_sha256, mapping_sha256=context.mapping_sha256,
                dry_run_sha256=context.dry_run_sha256, backup_sha256=context.backup_sha256,
                consent_sha256=context.consent_sha256, manifest_sha256=pin.manifest_sha256,
                issuer_key_id=pin.issuer_key_id, service_identity=pin.service_identity,
                policy_version=pin.policy_version, nonce="1234567890abcdef1234567890abcdef",
                issued_at=1000, expires_at=1060)
    return private, pin, context, body


def sign(private, body):
    signature = private.sign(_DOMAIN + canon(body))
    return canon({"body": body, "signature": base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")})


def check(envelope, pin, context, ledger=None, now=1030):
    return verify_synthetic_noop_ticket(envelope, provisioned=pin, expected=context,
                                        now_epoch=now, replay_ledger=ledger if ledger is not None else FakeLedger())


def test_valid_ticket_only_returns_nonclinical_noop_receipt():
    private, pin, context, body = make_fixture()
    receipt = check(sign(private, body), pin, context)
    assert receipt.verified_noop is True
    assert receipt.clinical_import_permitted is False
    assert receipt.tenant_id == "fixture-tenant-a"


@pytest.mark.parametrize("field,replacement", [
    ("version", 2), ("audience", "digital-crown:lot05:clinical"),
    ("operation", "CLINICAL_IMPORT"), ("tenant_id", "fixture-tenant-b"),
    ("source_sha256", sha("b")), ("target_sha256", sha("b")),
    ("mapping_sha256", sha("b")), ("dry_run_sha256", sha("b")),
    ("backup_sha256", sha("b")), ("consent_sha256", sha("b")),
    ("manifest_sha256", sha("b")), ("issuer_key_id", "fixture-key-rotated"),
    ("service_identity", "S-1-5-80-999"), ("policy_version", 2),
])
def test_re_signed_wrong_claim_still_denied(field, replacement):
    private, pin, context, body = make_fixture()
    body[field] = replacement
    with pytest.raises(SyntheticAuthorityDenied, match="CLAIM_MISMATCH"):
        check(sign(private, body), pin, context)


def test_modifying_signed_payload_without_signature_denied():
    private, pin, context, body = make_fixture()
    data = json.loads(sign(private, body))
    data["body"]["mapping_sha256"] = sha("f")
    with pytest.raises(SyntheticAuthorityDenied, match="INVALID_SIGNATURE"):
        check(canon(data), pin, context)


def test_forged_signer_denied_even_with_pinned_verifier():
    _, pin, context, body = make_fixture()
    attacker = Ed25519PrivateKey.generate()
    with pytest.raises(SyntheticAuthorityDenied, match="INVALID_SIGNATURE"):
        check(sign(attacker, body), pin, context)


def test_swapped_public_key_with_old_pin_denied():
    private, pin, context, body = make_fixture()
    attacker_public = Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    with pytest.raises(SyntheticAuthorityDenied, match="PIN_MISMATCH"):
        check(sign(private, body), replace(pin, public_key_raw=attacker_public), context)


def test_swapped_public_key_and_fingerprint_still_reject_original_signature():
    private, pin, context, body = make_fixture()
    attacker_public = Ed25519PrivateKey.generate().public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    untrusted_anchor = replace(pin, public_key_raw=attacker_public,
                               key_fingerprint_sha256=hashlib.sha256(attacker_public).hexdigest())
    with pytest.raises(SyntheticAuthorityDenied, match="INVALID_SIGNATURE"):
        check(sign(private, body), untrusted_anchor, context)


@pytest.mark.parametrize("updates,now", [
    ({"issued_at": 1040}, 1030), ({"expires_at": 1030}, 1030),
    ({"expires_at": 1121}, 1030), ({"issued_at": True}, 1030),
    ({"expires_at": False}, 1030), ({"nonce": "bad"}, 1030),
    ({"nonce": 1}, 1030),
])
def test_time_and_nonce_abuse_denied(updates, now):
    private, pin, context, body = make_fixture()
    body.update(updates)
    with pytest.raises(SyntheticAuthorityDenied):
        check(sign(private, body), pin, context, now=now)


def test_replay_denied_even_across_fresh_verifier_calls():
    private, pin, context, body = make_fixture()
    signed = sign(private, body)
    shared_ledger = FakeLedger()  # Simulates shared state; NOT crash persistence proof.
    check(signed, pin, context, shared_ledger)
    with pytest.raises(SyntheticAuthorityDenied, match="REPLAY_OR_LEDGER_INVALID"):
        check(signed, pin, context, shared_ledger)


def test_ledger_exception_fails_closed():
    class FaultyLedger:
        def consume_once(self, *unused):
            raise OSError("offline")
    private, pin, context, body = make_fixture()
    with pytest.raises(SyntheticAuthorityDenied, match="REPLAY_LEDGER_UNAVAILABLE"):
        check(sign(private, body), pin, context, FaultyLedger())


def test_no_ledger_fails_closed():
    private, pin, context, body = make_fixture()
    with pytest.raises(SyntheticAuthorityDenied, match="REPLAY_STORE_MISSING"):
        verify_synthetic_noop_ticket(sign(private, body), provisioned=pin,
                                     expected=context, now_epoch=1030, replay_ledger=None)


@pytest.mark.parametrize("change", ["unknown_field", "missing_field", "wrong_type", "bad_signature", "duplicate", "noncanonical", "oversize", "json_nan"])
def test_malformed_envelopes_fail_closed(change):
    private, pin, context, body = make_fixture()
    envelope = json.loads(sign(private, body))
    if change == "unknown_field":
        envelope["body"]["unexpected"] = "hi"
        data = sign(private, envelope["body"])
    elif change == "missing_field":
        del envelope["body"]["target_sha256"]
        data = sign(private, envelope["body"])
    elif change == "wrong_type":
        envelope["body"]["policy_version"] = True
        data = sign(private, envelope["body"])
    elif change == "bad_signature":
        envelope["signature"] = "oops"
        data = canon(envelope)
    elif change == "duplicate":
        data = sign(private, body).replace(b'"body":', b'"body":{},"body":', 1)
    elif change == "noncanonical":
        data = json.dumps(envelope).encode("ascii")
    elif change == "oversize":
        data = sign(private, body) + b" " * 8192
    else:
        data = sign(private, body).replace(b'"version":1', b'"version":NaN', 1)
    with pytest.raises(SyntheticAuthorityDenied):
        check(data, pin, context)


def test_invalid_clock_denied():
    private, pin, context, body = make_fixture()
    with pytest.raises(SyntheticAuthorityDenied, match="INVALID_CLOCK"):
        check(sign(private, body), pin, context, now=True)
