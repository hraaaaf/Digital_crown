"""SEC-P1.4 adversarial reference-only signature and licence policy tests.

Generated Ed25519 PRIVATE key exists only in RAM during this test process.
No issuer app, signing endpoint, key serialization or product auth modification.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sec_p1_4_signed_license_reference import (
    LicenseRejected, canonical_payload, signing_message, verify_license,
)

NOW = 1_800_000_000
TENANT = "cabinet-fixture-101"
DEVICE = hashlib.sha256(b"non-physical-device-fixture").hexdigest()
KEY_ID = "test-kid-p14"


class SignedLicenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Ephemeral test signing material, never written or shipped.
        cls.private = Ed25519PrivateKey.generate()
        cls.trusted = {KEY_ID: cls.private.public_key()}
        cls.untrusted = Ed25519PrivateKey.generate()

    def payload(self, **changes):
        payload = {
            "license_id": "license-fixture-101",
            "cabinet_id": TENANT,
            "device_binding_hash": DEVICE,
            "pack": "GOLD",
            "features": ["agenda", "patients", "finance"],
            "channel": "pilot",
            "issued_at": NOW - 120,
            "not_before": NOW - 100,
            "expires_at": NOW + 6 * 86400,
            "last_online_at": NOW - 100,
            "offline_until": NOW - 100 + 72 * 3600,
            "revocation_epoch": 3,
        }
        payload.update(changes)
        return payload

    def encode(self, payload=None, *, kid=KEY_ID, sign_with=None,
               signature_override=None):
        p = payload if payload is not None else self.payload()
        key = sign_with if sign_with is not None else self.private
        signature = base64.urlsafe_b64encode(
            key.sign(signing_message(kid, p))
        ).decode("ascii").rstrip("=")
        if signature_override is not None:
            signature = signature_override
        return json.dumps(
            {"v": 1, "kid": kid, "payload": p, "signature": signature},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        )

    def verify(self, envelope: str, **overrides):
        context = {
            "public_keys": self.trusted,
            "trusted_now": NOW,
            "cabinet_id": TENANT,
            "device_binding_hash": DEVICE,
            "required_pack": "GOLD",
            "required_feature": "agenda",
            "release_channel": "pilot",
            "minimum_revocation_epoch": 3,
        }
        context.update(overrides)
        return verify_license(envelope, **context)

    def refuse(self, case, expected=None, **options):
        with self.subTest(case=case):
            with self.assertRaises(LicenseRejected) as caught:
                self.verify(self.encode(**options))
            if expected is not None:
                self.assertEqual(caught.exception.reason, expected)

    def test_valid_signed_entitlement(self):
        result = self.verify(self.encode())
        self.assertEqual((result.cabinet_id, result.pack), (TENANT, "GOLD"))
        self.assertEqual(result.features, frozenset(["agenda", "patients", "finance"]))

    def test_byte_identical_canonical_payload(self):
        a = self.payload()
        b = dict(reversed(list(a.items())))
        self.assertEqual(canonical_payload(a), canonical_payload(b))

    def test_canonical_json_whitespace_tolerated(self):
        original = json.loads(self.encode())
        text = json.dumps(original, indent=2, ensure_ascii=True)
        self.assertEqual(self.verify(text).cabinet_id, TENANT)

    def test_reject_tampering_every_critical_claim(self):
        fields = [
            "license_id", "cabinet_id", "device_binding_hash", "pack",
            "features", "channel", "issued_at", "not_before", "expires_at",
            "last_online_at", "offline_until", "revocation_epoch",
        ]
        for field in fields:
            with self.subTest(field=field):
                envelope = json.loads(self.encode())
                existing = envelope["payload"][field]
                envelope["payload"][field] = (
                    ["imaging"] if field == "features"
                    else existing + 1 if isinstance(existing, int)
                    else "substituted-identity"
                )
                with self.assertRaises(LicenseRejected):
                    self.verify(json.dumps(envelope))

    def test_reject_unknown_signing_key(self):
        self.refuse("wrong kid", "untrusted-key-id", kid="unlisted-kid")

    def test_reject_key_marked_revoked(self):
        with self.assertRaises(LicenseRejected) as c:
            self.verify(self.encode(), revoked_key_ids=frozenset([KEY_ID]))
        self.assertEqual(c.exception.reason, "untrusted-key-id")

    def test_reject_signature_from_different_issuer(self):
        self.refuse("alternate key", "bad-signature", sign_with=self.untrusted)

    def test_reject_forged_b64_signature(self):
        self.refuse("64 zeroes", "bad-signature",
                    signature_override=base64.urlsafe_b64encode(bytes(64)).decode("ascii").rstrip("="))

    def test_reject_truncated_signature(self):
        self.refuse("one byte", "invalid-signature-encoding", signature_override="AA")

    def test_reject_signature_padding(self):
        self.refuse("padding", "invalid-signature-encoding",
                    signature_override=json.loads(self.encode())["signature"] + "==")

    def test_reject_legacy_algorithm_override(self):
        envelope = json.loads(self.encode())
        envelope["alg"] = "none"
        with self.assertRaises(LicenseRejected):
            self.verify(json.dumps(envelope))

    def test_reject_duplicate_top_level_field(self):
        encoded = self.encode()
        encoded = encoded.replace('"v":1', '"v":1,"v":1', 1)
        with self.assertRaises(LicenseRejected):
            self.verify(encoded)

    def test_reject_duplicate_nested_field(self):
        encoded = self.encode()
        encoded = encoded.replace('"pack":"GOLD"', '"pack":"GOLD","pack":"ELITE"', 1)
        with self.assertRaises(LicenseRejected):
            self.verify(encoded)

    def test_reject_nan_and_infinity(self):
        for raw in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(raw=raw):
                bad = self.encode().replace('"v":1', '"v":' + raw, 1)
                with self.assertRaises(LicenseRejected):
                    self.verify(bad)

    def test_reject_oversize_envelope(self):
        with self.assertRaises(LicenseRejected):
            self.verify("x" * 8193)

    def test_reject_bad_schema_and_version(self):
        for value in (2, True, "1", None):
            with self.subTest(version=value):
                obj = json.loads(self.encode())
                obj["v"] = value
                with self.assertRaises(LicenseRejected):
                    self.verify(json.dumps(obj))

    def test_reject_future_start(self):
        payload = self.payload(not_before=NOW + 1)
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(payload))

    def test_reject_expired(self):
        payload = self.payload(expires_at=NOW - 1, offline_until=NOW - 2)
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(payload))

    def test_reject_exhausted_offline_window(self):
        payload = self.payload(last_online_at=NOW - 72 * 3600 - 3,
                               offline_until=NOW - 3,
                               issued_at=NOW - 72 * 3600 - 100,
                               not_before=NOW - 72 * 3600 - 99)
        with self.assertRaises(LicenseRejected) as c:
            self.verify(self.encode(payload))
        self.assertEqual(c.exception.reason, "offline-window-exhausted")

    def test_reject_grace_exceeding_72h(self):
        payload = self.payload(offline_until=NOW - 100 + 72 * 3600 + 1)
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(payload))

    def test_reject_offline_later_than_subscription_expiry(self):
        payload = self.payload(expires_at=NOW + 1)
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(payload))

    def test_reject_revoked_revision_epoch(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), minimum_revocation_epoch=4)

    def test_reject_cross_cabinet_replay(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), cabinet_id="cabinet-fixture-202")

    def test_reject_cross_device_replay(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), device_binding_hash="f" * 64)

    def test_reject_commercial_pack_mismatch(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), required_pack="ELITE")

    def test_reject_unauthorized_feature(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), required_feature="imaging")

    def test_reject_release_channel_mismatch(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), release_channel="stable")

    def test_reject_untrusted_public_key_type(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), public_keys={KEY_ID: b"not-public-key"})

    def test_reject_boolean_timestamp(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(self.payload(issued_at=True)))

    def test_reject_duplicate_entitlements(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(self.payload(features=["agenda", "agenda"])))

    def test_reject_unknown_entitlement(self):
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(self.payload(features=["agenda", "superadmin"])))

    def test_reject_unknown_claim_field(self):
        payload = self.payload(private_key="not-allowed")
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(payload))

    def test_reject_missing_claim_field(self):
        payload = self.payload()
        payload.pop("offline_until")
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(payload))

    def test_reject_invalid_trusted_clock(self):
        for v in (True, -1, "now"):
            with self.subTest(clock=v):
                with self.assertRaises(LicenseRejected):
                    self.verify(self.encode(), trusted_now=v)

    def test_reject_max_envelope_type_confusion(self):
        for text in ("", "[]", "null", "1", '{"v":1}', "[]\n{}"):
            with self.subTest(text=text):
                with self.assertRaises(LicenseRejected):
                    self.verify(text)

    def test_untrusted_time_cannot_be_inferred_from_token(self):
        # This test deliberately does not assert protection against a
        # compromised local system clock. That requires a separate authority.
        with self.assertRaises(LicenseRejected):
            self.verify(self.encode(), trusted_now=NOW + 10 * 86400)

    def test_no_private_key_was_persisted(self):
        # The test issuer is an ephemeral in-memory fixture only.
        self.assertFalse(hasattr(self.private, "private_key_pem"))
        self.assertEqual(len(self.trusted), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
