"""LOT05.7-J6 Ed25519 signer and verifier run in distinct Python processes.

All private keys are transient and in a different process from verifier.
The test supplies the pin/trust anchor; NOT a production signing authority.
"""
from __future__ import annotations
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest
from backend.tests.fixtures import lot05j6_ed25519_ipc_lab as lab


class SeparateSignerVerifierLab(unittest.TestCase):
    def setUp(self):
        self.old = os.environ.get(lab.FLAG)
        os.environ[lab.FLAG] = "1"
        self.addCleanup(self.restore)
        self.temp = tempfile.TemporaryDirectory(prefix="lot05j6_fake_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.now = 1800000000
        self.body = {
            "nonce": secrets.token_hex(16), "owner": 17,
            "audience": lab.AUDIENCE, "path": lab.PATH,
            "sha256": hashlib.sha256(lab.PAYLOAD).hexdigest(),
            "issued": self.now, "expires": self.now + 120}
        self.signed = self.invoke("sign", {"body": self.body})
        self.assertEqual(self.signed.returncode, 0, self.signed.stderr)
        self.record = json.loads(self.signed.stdout)

    def restore(self):
        if self.old is None:
            os.environ.pop(lab.FLAG, None)
        else:
            os.environ[lab.FLAG] = self.old

    def invoke(self, role, request):
        return subprocess.run(
            [sys.executable, "-B", "-m",
             "backend.tests.fixtures.lot05j6_ed25519_ipc_lab", role],
            input=json.dumps(request), text=True, capture_output=True,
            timeout=20, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def request(self, *, envelope=None, trusted_pub=None, owner=17, now=None):
        return {
            "envelope": copy.deepcopy(envelope or self.record["envelope"]),
            "trusted_pub": trusted_pub or self.record["public_key"],
            "owner": owner, "now": self.now + 1 if now is None else now,
            "root": str(self.root)}

    def denied(self, request):
        outcome = self.invoke("verify", request)
        self.assertNotEqual(outcome.returncode, 0, outcome.stdout)
        self.assertIn("J6_DENIED_", outcome.stderr)

    def test_01_true_separate_processes_accept_signature(self):
        response = self.invoke("verify", self.request())
        self.assertEqual(response.returncode, 0, response.stderr)
        proof = json.loads(response.stdout)
        self.assertTrue(proof["accepted"])
        self.assertTrue(proof["fake_only"])
        self.assertNotEqual(proof["verifier_pid"], self.record["signer_pid"])
        self.assertNotEqual(proof["verifier_pid"], os.getpid())

    def test_02_second_verifier_process_replay_denied(self):
        self.assertEqual(self.invoke("verify", self.request()).returncode, 0)
        self.denied(self.request())

    def test_03_modified_claim_denied(self):
        envelope = copy.deepcopy(self.record["envelope"])
        envelope["body"]["owner"] = 99
        self.denied(self.request(envelope=envelope))

    def test_04_signature_tamper_denied(self):
        envelope = copy.deepcopy(self.record["envelope"])
        envelope["sig"] = base64.b64encode(b"\0" * 64).decode("ascii")
        self.denied(self.request(envelope=envelope))

    def test_05_unpinned_public_key_denied(self):
        foreign = self.invoke("sign", {"body": self.body})
        self.assertEqual(foreign.returncode, 0, foreign.stderr)
        self.denied(self.request(trusted_pub=json.loads(foreign.stdout)["public_key"]))

    def test_06_owner_mismatch_denied(self):
        self.denied(self.request(owner=99))

    def test_07_expired_or_early_denied(self):
        self.denied(self.request(now=self.now - 1))
        self.denied(self.request(now=self.now + 120))

    def test_08_broken_ledger_fails_closed(self):
        (self.root / "j6-nonces.sqlite").write_bytes(b"INVALID_SQLITE")
        self.denied(self.request())

    def test_09_missing_fake_flag_denied(self):
        os.environ[lab.FLAG] = "0"
        self.denied(self.request())

    def test_10_fake_signer_not_a_clinical_applicative_authority(self):
        self.assertNotIn("private_key", self.record)
        self.assertNotIn("seed", self.record)
        self.assertFalse((self.root / "patients.db").exists())
        self.assertFalse((self.root / "clinical_vault.db").exists())

    def test_11_fake_replay_ledger_symlink_denied(self):
        decoy = self.root / "fake-target-ledger"
        decoy.write_bytes(b"SYNTHETIC")
        (self.root / "j6-nonces.sqlite").symlink_to(decoy)
        self.denied(self.request())

    def test_12_bad_audience_denied_even_if_signed(self):
        evil = copy.deepcopy(self.body)
        evil["audience"] = "REAL_CLINICAL_WORKER"
        response = self.invoke("sign", {"body": evil})
        self.assertNotEqual(response.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
