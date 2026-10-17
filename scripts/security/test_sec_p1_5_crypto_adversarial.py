"""SEC-P1.5 adversarial edge cases against the Ed25519 reference contract.

Uses only in-process ephemeral signing keys and synthetic cabinet/device IDs.
No production integration, signing endpoint, key persistence or patient data.
"""
from __future__ import annotations

import base64
import hashlib
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from sec_p1_4_signed_license_reference import (
    LicenseRejected, signing_message, verify_license,
)

NOW = 1_800_000_000
KID = "synthetic-p15-key"
CABINET = "synthetic-cabinet-101"
DEVICE_HASH = hashlib.sha256(b"fictional-station-id").hexdigest()


class IndependentAdversarialEdges(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.issuer = Ed25519PrivateKey.generate()
        cls.trusted = {KID: cls.issuer.public_key()}

    def claims(self, **overrides):
        base = {
            "license_id": "synthetic-lic-101",
            "cabinet_id": CABINET,
            "device_binding_hash": DEVICE_HASH,
            "pack": "GOLD",
            "features": ["agenda", "patients"],
            "channel": "pilot",
            "issued_at": NOW - 1000,
            "not_before": NOW - 500,
            "expires_at": NOW + 6 * 86400,
            "last_online_at": NOW - 200,
            "offline_until": NOW - 200 + 72 * 3600,
            "revocation_epoch": 7,
        }
        base.update(overrides)
        return base

    def signed(self, payload=None):
        body = self.claims() if payload is None else payload
        sig = self.issuer.sign(signing_message(KID, body))
        return json.dumps({
            "v": 1, "kid": KID, "payload": body,
            "signature": base64.urlsafe_b64encode(sig).decode("ascii").rstrip("="),
        }, sort_keys=True, separators=(",", ":"))

    def check(self, data, **options):
        ctx = dict(
            public_keys=self.trusted,
            trusted_now=NOW,
            cabinet_id=CABINET,
            device_binding_hash=DEVICE_HASH,
            required_pack="GOLD",
            required_feature="agenda",
            release_channel="pilot",
            minimum_revocation_epoch=7,
        )
        ctx.update(options)
        return verify_license(data, **ctx)

    def expect_reason(self, data, expected, **options):
        with self.assertRaises(LicenseRejected) as error:
            self.check(data, **options)
        self.assertEqual(error.exception.reason, expected)

    def test_nominal_valid_signature(self):
        self.assertEqual(self.check(self.signed()).cabinet_id, CABINET)

    def test_unpaired_high_surrogate_is_fail_closed(self):
        self.expect_reason("\ud800", "invalid-envelope")

    def test_unpaired_low_surrogate_is_fail_closed(self):
        self.expect_reason("\udfff", "invalid-envelope")

    def test_future_online_check_rejected_with_valid_signature(self):
        signed = self.signed(self.claims(
            last_online_at=NOW + 1,
            offline_until=NOW + 1 + 100,
        ))
        self.expect_reason(signed, "future-online-validation")

    def test_online_check_at_current_trusted_time_is_valid(self):
        signed = self.signed(self.claims(
            last_online_at=NOW,
            offline_until=NOW + 72 * 3600,
        ))
        self.assertEqual(self.check(signed).pack, "GOLD")

    def test_subscription_expiry_exact_second_is_exclusive(self):
        signed = self.signed(self.claims(expires_at=NOW, offline_until=NOW - 10))
        self.expect_reason(signed, "expired")

    def test_offline_expiry_exact_second_is_exclusive(self):
        signed = self.signed(self.claims(offline_until=NOW))
        self.expect_reason(signed, "offline-window-exhausted")

    def test_offline_expiry_one_second_before_is_valid(self):
        signed = self.signed(self.claims(offline_until=NOW + 1))
        self.assertEqual(self.check(signed).pack, "GOLD")

    def test_invalid_trusted_keys_mapping_rejected(self):
        self.expect_reason(self.signed(), "invalid-verifier-context", public_keys=123)

    def test_invalid_revoked_key_ids_container_rejected(self):
        self.expect_reason(self.signed(), "invalid-verifier-context", revoked_key_ids=None)

    def test_present_revoked_key_denied(self):
        self.expect_reason(self.signed(), "untrusted-key-id", revoked_key_ids=frozenset({KID}))

    def test_epoch_from_trusted_source_must_match(self):
        self.expect_reason(self.signed(), "revoked-epoch", minimum_revocation_epoch=8)

    def test_cross_cabinet_cannot_reuse_signed_lease(self):
        self.expect_reason(self.signed(), "identity-mismatch", cabinet_id="synthetic-cabinet-202")

    def test_cross_device_cannot_reuse_signed_lease(self):
        self.expect_reason(self.signed(), "identity-mismatch", device_binding_hash="f" * 64)

    def test_client_cannot_add_entitlement_to_signed_payload(self):
        altered = json.loads(self.signed())
        altered["payload"]["features"].append("imaging")
        self.expect_reason(json.dumps(altered), "bad-signature")

    def test_client_cannot_extend_signed_offline_window(self):
        altered = json.loads(self.signed())
        altered["payload"]["offline_until"] += 1
        self.expect_reason(json.dumps(altered), "bad-signature")

    def test_invalid_context_cannot_enable_unknown_feature(self):
        self.expect_reason(self.signed(), "invalid-verifier-context", required_feature="unrestricted")

    def test_unsigned_legacy_envelope_refused(self):
        old = json.loads(self.signed())
        old.pop("signature")
        self.expect_reason(json.dumps(old), "invalid-envelope")

    def test_empty_public_key_manifest_refused(self):
        self.expect_reason(self.signed(), "untrusted-key-id", public_keys={})

    def test_no_clinic_identifier_in_public_exception(self):
        with self.assertRaises(LicenseRejected) as error:
            self.check(self.signed(), cabinet_id="synthetic-cabinet-202")
        self.assertNotIn(CABINET, str(error.exception))
        self.assertNotIn(DEVICE_HASH, str(error.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
