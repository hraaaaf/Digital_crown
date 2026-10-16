"""LOT06-N witness/client separate-PROCESS synthetic loopback experiments."""
from __future__ import annotations

import base64
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.imaging_gateway.durable_cas_lab import (
    GENESIS_MAC, apply, audit, event, initialize, signer_pub,
)
from tools.imaging_gateway.independent_witness_lab import (
    RESP_DOMAIN, CasRefusal, auth_request, canonical, proof_bytes,
    request_shape, verify_request, verify_response, b64,
)


def private(key: Ed25519PrivateKey) -> str:
    return b64(key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()))


class IndependentWitnessSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dc06m-cas-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "witness-synthetic.sqlite"
        self.scope = secrets.token_hex(16)
        self.witness = Ed25519PrivateKey.generate()
        self.client = Ed25519PrivateKey.generate()
        self.wpub = signer_pub(self.witness)
        self.cpub = signer_pub(self.client)
        initialize(self.path, self.scope, self.wpub)
        self.proc = None
        self.start()

    def start(self):
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "tools.imaging_gateway.independent_witness_lab",
             "--lab-server", "--db", str(self.path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True)
        boot = {"witness_private_b64": private(self.witness),
                "client_pub_b64": b64(self.cpub)}
        self.proc.stdin.write(json.dumps(boot) + "\n")
        self.proc.stdin.close()
        ready_line = self.proc.stdout.readline().strip()
        if not ready_line:
            raise AssertionError("Synthetic witness server did not start")
        ready = json.loads(ready_line)
        self.assertEqual(ready["status"], "READY_LAB_ONLY")
        self.port = ready["port"]
        self.addCleanup(self.stop)

    def stop(self):
        if self.proc is None:
            return
        p = self.proc
        self.proc = None
        if p.poll() is None:
            p.terminate()
        try:
            p.wait(timeout=8)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=5)
        p.stdout.close()
        p.stderr.close()

    def e(self, seq=0, mac=GENESIS_MAC, op=None, after=None):
        return event(self.scope, op or secrets.token_hex(16), seq, mac,
                     after or secrets.token_hex(32))

    def req(self, method, e=None, op=None, challenge=None):
        if method in ("APPLY", "DROP_AFTER_COMMIT"):
            self.assertIsNotNone(e)
            op = e["op_id"]
        return {"protocol": "DC06N_SYNTHETIC_V1", "method": method,
                "scope": self.scope, "challenge": challenge or secrets.token_hex(16),
                "op_id": op or secrets.token_hex(16),
                "event": e}

    def call(self, req, client=None, pub=None, port=None, gate=None):
        wire = {"client_private_b64": private(client or self.client),
                "witness_pub_b64": b64(pub or self.wpub), "request": req}
        argv = [sys.executable, "-m", "tools.imaging_gateway.independent_witness_lab",
                "--lab-client", "--port", str(self.port if port is None else port)]
        if gate is not None:
            argv.extend(["--gate", str(gate)])
        result = subprocess.run(
            argv,
            input=json.dumps(wire) + "\n", capture_output=True, text=True, timeout=12)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        return json.loads(result.stdout)

    def test_two_processes_same_parent_one_cas_winner(self):
        r1, r2 = self.req("APPLY", self.e()), self.req("APPLY", self.e())
        gate = Path(self.temp.name) / "barrier-go"
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(self.call, r1, gate=gate)
            f2 = pool.submit(self.call, r2, gate=gate)
            deadline = time.monotonic() + 10
            while len(list(gate.parent.glob("ready-*"))) < 2 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(len(list(gate.parent.glob("ready-*"))), 2,
                             "Both client processes must reach the barrier")
            gate.touch()
            out = [f1.result(timeout=15), f2.result(timeout=15)]
        self.assertEqual(sorted(x["status"] for x in out),
                         ["DECIDED_LAB_ONLY", "UNKNOWN_NO_AUTHORITY"], out)
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)

    def test_two_processes_same_request_idempotent_same_receipt(self):
        req = self.req("APPLY", self.e())
        gate = Path(self.temp.name) / "barrier-go"
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(self.call, req, gate=gate)
            f2 = pool.submit(self.call, req, gate=gate)
            deadline = time.monotonic() + 10
            while len(list(gate.parent.glob("ready-*"))) < 2 and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(len(list(gate.parent.glob("ready-*"))), 2,
                             "Both client processes must reach the barrier")
            gate.touch()
            out = [f1.result(timeout=15), f2.result(timeout=15)]
        self.assertEqual([x["status"] for x in out],
                         ["DECIDED_LAB_ONLY", "DECIDED_LAB_ONLY"], out)
        self.assertEqual(out[0]["receipt_b64"], out[1]["receipt_b64"])
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)

    def test_lost_ack_after_durable_commit_rejoin_same_op_id(self):
        e = self.e()
        lost = self.call(self.req("DROP_AFTER_COMMIT", e))
        self.assertEqual(lost["status"], "UNKNOWN_NO_AUTHORITY")
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)
        found = self.call(self.req("LOOKUP", op=e["op_id"]))
        self.assertEqual(found["status"], "DECIDED_LAB_ONLY")
        again = self.call(self.req("APPLY", e))
        self.assertEqual(again["receipt_b64"], found["receipt_b64"])
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)

    def test_offline_witness_fails_closed_then_recovers(self):
        self.stop()
        lost = self.call(self.req("APPLY", self.e()))
        self.assertEqual(lost["status"], "UNKNOWN_NO_AUTHORITY")
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 0)
        self.start()
        result = self.call(self.req("APPLY", self.e()))
        self.assertEqual(result["status"], "DECIDED_LAB_ONLY")

    def test_server_restart_from_committed_sqlite_rejoins(self):
        e = self.e()
        self.assertEqual(self.call(self.req("APPLY", e))["status"], "DECIDED_LAB_ONLY")
        self.stop()
        self.start()  # harness re-injects test signer; NO custody proof
        got = self.call(self.req("LOOKUP", op=e["op_id"]))
        self.assertEqual(got["status"], "DECIDED_LAB_ONLY")
        self.assertEqual(got["seq"], 1)

    def test_wrong_client_key_does_not_get_signed_ack(self):
        got = self.call(self.req("APPLY", self.e()), client=Ed25519PrivateKey.generate())
        self.assertEqual(got["status"], "UNKNOWN_NO_AUTHORITY")
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 0)

    def test_wrong_server_pin_does_not_get_authorization(self):
        got = self.call(self.req("APPLY", self.e()),
                        pub=signer_pub(Ed25519PrivateKey.generate()))
        self.assertEqual(got["status"], "UNKNOWN_NO_AUTHORITY")
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)
        # The witness may commit, but client cannot claim trusted ACK with wrong pin.

    def test_changed_op_id_payload_rebind_not_acknowledged(self):
        e = self.e()
        self.assertEqual(self.call(self.req("APPLY", e))["status"], "DECIDED_LAB_ONLY")
        changed = {**e, "manifest_digest": "f" * 64}
        got = self.call(self.req("APPLY", changed))
        self.assertEqual(got["status"], "UNKNOWN_NO_AUTHORITY")
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)

    def test_historical_receipt_is_only_historical(self):
        one = self.e()
        self.call(self.req("APPLY", one))
        two = self.e(seq=1, mac=one["after_mac"])
        self.call(self.req("APPLY", two))
        old = self.call(self.req("LOOKUP", op=one["op_id"]))
        self.assertEqual(old["status"], "HISTORICAL_ONLY")
        self.assertEqual(old["seq"], 2)

    def test_fresh_signed_head_and_stale_challenge_refusal(self):
        req = self.req("HEAD")
        got = self.call(req)
        self.assertEqual(got["status"], "HEAD_ONLY")
        self.assertEqual(got["seq"], 0)
        # Authentic but replayed response: valid signature fails NEW nonce binding.
        proof = got.copy()
        packet = {"proof": proof, "signature_b64": b64(self.witness.sign(proof_bytes(proof)))}
        with self.assertRaisesRegex(CasRefusal, "RESPONSE_BINDING_REFUSE"):
            verify_response(packet, self.wpub, self.req("HEAD", op=req["op_id"]))

    def test_bad_signature_and_schema_refused(self):
        req = self.req("APPLY", self.e())
        packet = auth_request(req, self.client)
        verify_request(packet, self.cpub)
        with self.assertRaises(CasRefusal):
            verify_request(packet, signer_pub(Ed25519PrivateKey.generate()))
        with self.assertRaises(CasRefusal):
            request_shape({**req, "patient_id": "DENIED"})
        forged = {"request": {**req, "challenge": secrets.token_hex(16)},
                  "signature_b64": packet["signature_b64"]}
        with self.assertRaises(CasRefusal):
            verify_request(forged, self.cpub)

    def test_corrupted_ledger_fails_closed_over_transport(self):
        self.stop()
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE authority_head SET seq=123")
        self.start()
        got = self.call(self.req("HEAD"))
        self.assertEqual(got["status"], "UNKNOWN_NO_AUTHORITY")

    def test_full_db_rollback_old_head_can_still_be_signed(self):
        one = self.e()
        self.assertEqual(self.call(self.req("APPLY", one))["status"], "DECIDED_LAB_ONLY")
        old = Path(self.temp.name) / "old.db"
        self.stop()
        shutil.copy2(self.path, old)
        self.start()
        two = self.e(seq=1, mac=one["after_mac"])
        self.assertEqual(self.call(self.req("APPLY", two))["status"], "DECIDED_LAB_ONLY")
        self.stop()
        shutil.copy2(old, self.path)
        self.start()
        # A freshly challenged signature from a rolled-back witness is NOT global freshness.
        result = self.call(self.req("HEAD"))
        self.assertEqual(result["status"], "HEAD_ONLY")
        self.assertEqual(result["seq"], 1)
        self.assertEqual(audit(self.path, self.scope, self.wpub)[2], 1)


if __name__ == "__main__":
    unittest.main()
