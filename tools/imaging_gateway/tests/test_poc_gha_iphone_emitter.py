"""LOT06-M synthetic transport-only refusal tests; no phone or physical CAS claims."""
import base64
import copy
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from tools.imaging_gateway.poc_gha_iphone_emitter import create_demo, verify_demo, canonical

SHA = "a" * 40
RUN = "38813168061"


class SyntheticPhoneReceiptTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.pub = create_demo(SHA, RUN)

    def valid(self, packet=None, pub=None, sha=SHA, run_id=RUN):
        return verify_demo(self.packet if packet is None else packet,
                           self.pub if pub is None else pub,
                           expected_sha=sha, expected_run_id=run_id)

    def test_correct_receipt_non_authorizing(self):
        d = self.valid()
        self.assertEqual(d["decision"], "DEMO_NOT_AUTHORITY_ACK")
        self.assertEqual(d["source_sha"], SHA)

    def test_modified_signed_payload_refused(self):
        p = copy.deepcopy(self.packet)
        raw = bytearray(base64.b64decode(p["payload_b64"]))
        raw[-1] ^= 1
        p["payload_b64"] = base64.b64encode(raw).decode()
        with self.assertRaises(ValueError): self.valid(packet=p)

    def test_wrong_independent_public_key_refused(self):
        other = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        with self.assertRaises(ValueError): self.valid(pub=base64.b64encode(other).decode())

    def test_signed_source_sha_run_id_bound(self):
        with self.assertRaises(ValueError): self.valid(sha="b" * 40)
        with self.assertRaises(ValueError): self.valid(run_id="42")

    def test_altered_signature_refused(self):
        p = dict(self.packet)
        p["signature_b64"] = base64.b64encode(b"\0" * 64).decode()
        with self.assertRaises(ValueError): self.valid(packet=p)

    def test_bad_schema_and_extra_patient_data_refused(self):
        d = self.valid()
        d["patient_id"] = "DO_NOT_ALLOW"
        with self.assertRaises(ValueError): canonical(d)
        d.pop("patient_id")
        d["decision"] = "ACK_CLINICAL"
        with self.assertRaises(ValueError): canonical(d)

    def test_missing_or_noncanonical_packet_refused(self):
        with self.assertRaises(ValueError): self.valid(packet={})
        p = dict(self.packet)
        p["payload_b64"] = "notbase64"
        with self.assertRaises(ValueError): self.valid(packet=p)

    def test_per_run_key_and_opaque_operation_are_ephemeral(self):
        other, pub2 = create_demo(SHA, RUN)
        self.assertNotEqual(self.pub, pub2)
        self.assertNotEqual(self.valid()["operation_id"],
                            verify_demo(other, pub2, expected_sha=SHA, expected_run_id=RUN)["operation_id"])


if __name__ == "__main__":
    unittest.main()
