"""Synthetic Ed25519 vectors: fail-closed binding without physical authority."""
from dataclasses import replace
import hashlib
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.imaging_gateway import journal_lab as j
from tools.imaging_gateway import signed_witness_receipt_lab as w


class SignedReceiptTests(unittest.TestCase):
    def setUp(self):
        # TEST-ONLY ephemeral private key; no identity/key stored or deployed.
        self.private=Ed25519PrivateKey.generate()
        pub=self.private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        kid=hashlib.sha256(pub).hexdigest()[:32]
        self.pin=w.AuthorityPin(
            "independent-lab-witness","epoch-01","a"*32,kid,pub)
        self.prev=j.TrustedAnchor(4,"1"*64)
        self.head=j.TrustedAnchor(5,"2"*64)
        self.manifest="3"*64
        self.op="4"*32
        self.envelope=w.DecisionEnvelope(
            self.pin.authority_id,self.pin.epoch,self.pin.opaque_scope,
            kid,self.op,self.prev,self.head,self.manifest)
        self.signed=self.sign(self.envelope)

    def sign(self,envelope):
        return w.SignedDecision(
            envelope,self.private.sign(w.canonical_envelope(envelope)))

    def check(self,receipt=None,pin=None,head=None,**changes):
        return w.verify_read_only(
            self.signed if receipt is None else receipt,
            self.pin if pin is None else pin,
            expected_operation_id=changes.get("operation_id",self.op),
            expected_previous=changes.get("previous",self.prev),
            expected_transition_digest=changes.get("digest",self.manifest),
            supplied_current_head=self.head if head is None else head)

    def test_signed_correct_current_head_non_authorizing(self):
        self.assertEqual(self.check().code,
                         "SIGNED_MATCH_NO_AUTHORIZATION")
        self.assertNotIn("ACK",self.check().code)

    def test_valid_old_receipt_with_newer_head_is_historical_not_ack(self):
        newer=j.TrustedAnchor(6,"5"*64)
        self.assertEqual(self.check(head=newer).code,
                         "SIGNED_HISTORICAL_ONLY_NO_AUTHORIZATION")

    def test_changed_signature_or_payload_refuses(self):
        bad=replace(self.signed,signature=b"\x00"*64)
        with self.assertRaisesRegex(w.SignedReceiptLabError,"SIGNATURE_REFUSE"):
            self.check(receipt=bad)
        forged=replace(self.envelope,after=j.TrustedAnchor(5,"0"*64))
        with self.assertRaisesRegex(w.SignedReceiptLabError,"SIGNATURE_REFUSE"):
            self.check(receipt=replace(self.signed,envelope=forged))

    def test_wrong_pin_and_epoch_scope_keyid_refuses(self):
        stranger=Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
        wrong_pin=replace(self.pin,public_key=stranger,
            public_key_id=hashlib.sha256(stranger).hexdigest()[:32])
        for pin in (wrong_pin,replace(self.pin,epoch="epoch-02"),
                    replace(self.pin,opaque_scope="b"*32)):
            with self.subTest(pin=pin.epoch+pin.opaque_scope):
                with self.assertRaisesRegex(
                    w.SignedReceiptLabError,"AUTHORITY_BINDING_REFUSE|SIGNATURE_REFUSE"):
                    self.check(pin=pin)
        with self.assertRaisesRegex(w.SignedReceiptLabError,"PIN_INVALID"):
            self.check(pin=replace(self.pin,public_key_id="f"*32))

    def test_operation_prior_anchor_and_manifest_mismatch_refuse(self):
        for payload in ({"operation_id":"5"*32},
                        {"previous":j.TrustedAnchor(4,"f"*64)},
                        {"digest":"f"*64}):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(
                        w.SignedReceiptLabError,"REQUEST_BINDING_REFUSE"):
                    self.check(**payload)

    def test_current_head_lower_or_same_sequence_fork_refuse(self):
        with self.assertRaisesRegex(
            w.SignedReceiptLabError,"CURRENT_HEAD_ROLLBACK_REFUSE"):
            self.check(head=self.prev)
        with self.assertRaisesRegex(
            w.SignedReceiptLabError,"CURRENT_HEAD_FORK_REFUSE"):
            self.check(head=j.TrustedAnchor(5,"f"*64))

    def test_malformed_body_signature_and_transition_refuse(self):
        forged=replace(self.envelope,decision="UNKNOWN")
        with self.assertRaisesRegex(
            w.SignedReceiptLabError,"RECEIPT_SHAPE_REFUSE"):
            w.canonical_envelope(forged)
        malformed=replace(self.envelope,after=j.TrustedAnchor(8,"f"*64))
        with self.assertRaisesRegex(
            w.SignedReceiptLabError,"RECEIPT_SHAPE_REFUSE"):
            w.canonical_envelope(malformed)
        with self.assertRaisesRegex(
            w.SignedReceiptLabError,"RECEIPT_SHAPE_REFUSE"):
            self.check(receipt=replace(self.signed,signature=b"x"))

    def test_stale_head_and_signed_receipt_still_match_if_both_rolled_back(self):
        # VITAL NEGATIVE PROOF: client-supplied head is not a remote oracle.
        old=self.check(head=self.head)
        self.assertEqual(old.code,"SIGNED_MATCH_NO_AUTHORIZATION")
        # The lab CANNOT distinguish this from a later actual external head.
        # A durable independent read-only current-head query is a HUMAN GATE.

    def test_valid_signature_does_not_enforce_unique_operation_cas(self):
        # Separate signer with stolen/available key could sign 2 forks;
        # pure verification cannot arbitrate them or prove monotonicity.
        other=j.TrustedAnchor(5,"f"*64)
        second=self.sign(replace(self.envelope,after=other))
        self.assertEqual(self.check().code,"SIGNED_MATCH_NO_AUTHORIZATION")
        self.assertEqual(self.check(receipt=second,head=other).code,
                         "SIGNED_MATCH_NO_AUTHORIZATION")

if __name__=="__main__":
    unittest.main()
