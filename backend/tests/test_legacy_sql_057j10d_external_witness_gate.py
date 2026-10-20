"""J10D real Ed25519 verification with CI-generated FAKE witness, DENY-only.

These tests prove format/integrity/freshness and *do not* prove an independent
external trust root, signing service, counter, Windows powercut or any clinical GO.
"""
import base64
import copy
import subprocess
import sys
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.tests.fixtures import lot05j10d_external_witness_gate as gate


class J10DExternalWitnessSpecimen(unittest.TestCase):
    def setUp(self):
        self.signer = Ed25519PrivateKey.generate()  # CI FAKE only
        self.public = self.signer.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.now = 1_800_000_100
        self.context = dict(
            raw_fake_public_key=self.public,
            expected_device="DC-LAB-FAKE-WIN-01",
            expected_challenge="b" * 32,
            expected_ledger_id="c" * 24,
            expected_signer_sha256="d" * 64,
            expected_consumer_sha256="e" * 64,
            last_externally_confirmed_checkpoint=41,
            now=self.now,
        )
        self.payload = dict(
            schema=gate.SCHEMA,
            device=self.context["expected_device"],
            challenge=self.context["expected_challenge"],
            ledger_id=self.context["expected_ledger_id"],
            signer_sha256=self.context["expected_signer_sha256"],
            consumer_sha256=self.context["expected_consumer_sha256"],
            checkpoint=42,
            issued_at=self.now - 5,
            expires_at=self.now + 30,
            decision="DENY_ONLY_LAB",
        )

    def receipt(self, payload=None):
        fields=copy.deepcopy(self.payload if payload is None else payload)
        signature=self.signer.sign(gate.canonical_payload(fields))
        return dict(payload=fields,signature=base64.b64encode(signature).decode("ascii"))

    def check(self, receipt, **updates):
        options=dict(self.context,**updates)
        return gate.evaluate_fake_witness(receipt, **options)

    def test_01_signed_fake_ed25519_receipt_remains_deny_only(self):
        result=self.check(self.receipt())
        self.assertEqual(result, "DENY_J10D_WITNESS_CRYPTO_VALID_FAKE_ROOT_IS_NOT_INDEPENDENT")
        self.assertNotIn("ALLOW",result)
        print("J10D_FAKE_ED25519_CRYPTO_OK_BUT_NO_INDEPENDENT_ROOT_PASS")

    def test_02_product_gate_never_go_even_with_verified_fixture(self):
        self.assertEqual(gate.product_readiness(),
                         "DENY_J10D_WITNESS_EXTERNAL_AUTHORITY_NOT_ENROLLED")
        self.assertEqual(gate.product_readiness(self.receipt(),self.public),
                         "DENY_J10D_WITNESS_EXTERNAL_AUTHORITY_NOT_ENROLLED")
        print("J10D_EXTERNAL_AUTHORITY_ABSENT_PRODUCT_FAIL_CLOSED_PASS")

    def test_03_missing_root_and_attestation_fail_closed(self):
        self.assertEqual(self.check(self.receipt(),raw_fake_public_key=b""),
                         "DENY_J10D_WITNESS_ROOT_UNAVAILABLE")
        self.assertEqual(self.check(None),"DENY_J10D_WITNESS_STRUCTURE")

    def test_04_tampered_signed_checkpoint_never_accepted(self):
        receipt=self.receipt()
        receipt["payload"]["checkpoint"]=43
        self.assertEqual(self.check(receipt),"DENY_J10D_WITNESS_SIGNATURE_OR_MALFORMED")

    def test_05_wrong_device_or_binary_hash_denied(self):
        receipt=self.receipt()
        for field, change in [
            ("expected_device","wrong-host"),
            ("expected_ledger_id","f"*24),
            ("expected_signer_sha256","f"*64),
            ("expected_consumer_sha256","f"*64),
        ]:
            with self.subTest(field=field):
                self.assertEqual(self.check(receipt,**{field:change}),
                                 "DENY_J10D_WITNESS_SCOPE")

    def test_06_wrong_request_challenge_and_replayed_receipt_denied(self):
        receipt=self.receipt()
        self.assertEqual(self.check(receipt,expected_challenge="f"*32),
                         "DENY_J10D_WITNESS_SCOPE")
        self.assertEqual(self.check(receipt,last_externally_confirmed_checkpoint=42),
                         "DENY_J10D_WITNESS_ROLLBACK_OR_REPLAY")
        self.assertEqual(self.check(receipt,last_externally_confirmed_checkpoint=43),
                         "DENY_J10D_WITNESS_ROLLBACK_OR_REPLAY")
        print("J10D_WITNESS_FLOOR_REPLAY_AND_ROLLBACK_REJECTED_LAB_PASS")

    def test_07_expired_future_and_overlong_valid_receipts_denied(self):
        for field,value in [
            ("issued_at",self.now - 120),
            ("issued_at",self.now + 6),
            ("expires_at",self.now),
            ("expires_at",self.now+70),
        ]:
            with self.subTest(field=field,value=value):
                p=dict(self.payload,**{field:value})
                self.assertEqual(self.check(self.receipt(p)),"DENY_J10D_WITNESS_TIME")

    def test_08_broken_schema_unexpected_fields_and_bool_counter_denied(self):
        p=dict(self.payload,schema="UNRELATED")
        self.assertEqual(self.check(self.receipt(p)),"DENY_J10D_WITNESS_SCHEMA")
        p=dict(self.payload,unverified_override="allow")
        self.assertEqual(self.check(self.receipt(p)),"DENY_J10D_WITNESS_STRUCTURE")
        p=dict(self.payload,checkpoint=True)
        self.assertEqual(self.check(self.receipt(p)),"DENY_J10D_WITNESS_STRUCTURE")
        self.assertEqual(self.check(self.receipt(),last_externally_confirmed_checkpoint=True),
                         "DENY_J10D_WITNESS_CHECKPOINT_FLOOR")

    def test_09_wrong_signature_and_fake_root_rotation_denied(self):
        r=self.receipt()
        other=Ed25519PrivateKey.generate()
        other_public=other.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,format=serialization.PublicFormat.Raw)
        self.assertEqual(self.check(r,raw_fake_public_key=other_public),
                         "DENY_J10D_WITNESS_SIGNATURE_OR_MALFORMED")
        r["signature"]="!" * 88
        self.assertEqual(self.check(r),"DENY_J10D_WITNESS_SIGNATURE_OR_MALFORMED")

    def test_10_no_unsigned_allow_or_confused_decision(self):
        p=dict(self.payload,decision="ALLOW")
        self.assertEqual(self.check(self.receipt(p)),"DENY_J10D_WITNESS_SCHEMA")
        for r in [dict(payload=self.payload),dict(payload=self.payload,signature="A"*88,allow=True)]:
            self.assertEqual(self.check(r),"DENY_J10D_WITNESS_STRUCTURE")

    def test_11_canonical_payload_independent_of_map_key_order(self):
        ascending=dict(sorted(self.payload.items()))
        descending=dict(sorted(self.payload.items(),reverse=True))
        self.assertEqual(gate.canonical_payload(ascending),gate.canonical_payload(descending))
        self.assertEqual(self.check(self.receipt(ascending)),
                         "DENY_J10D_WITNESS_CRYPTO_VALID_FAKE_ROOT_IS_NOT_INDEPENDENT")

    def test_12_executable_gate_returns_nonzero_and_no_go(self):
        run=subprocess.run(
            [sys.executable,"-m","backend.tests.fixtures.lot05j10d_external_witness_gate"],
            capture_output=True,text=True,timeout=10,
        )
        self.assertEqual(run.returncode,3,run.stderr)
        self.assertEqual(run.stdout.strip(),"DENY_J10D_WITNESS_EXTERNAL_AUTHORITY_NOT_ENROLLED")
        self.assertNotIn("ALLOW",run.stdout)
        print("J10D_UNENROLLED_EXTERNAL_WITNESS_CLI_DENY_NONZERO_PASS")


if __name__=="__main__":
    unittest.main(verbosity=2)
