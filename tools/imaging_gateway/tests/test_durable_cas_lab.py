"""Synthetic disposable SQLite CAS and process-death matrix; no patient or physical hardware."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
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
    AUTHORITY, EPOCH, GENESIS_MAC, CasRefusal, apply, audit, canonical,
    event, event_bytes, initialize, lookup, signer_pub, verify_receipt,
)


class DurableCasSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dc06m-cas-synthetic-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "witness-synthetic.sqlite"
        self.scope = secrets.token_hex(16)
        self.signer = Ed25519PrivateKey.generate()  # ephemeral: NEVER stored in DB
        self.pub = signer_pub(self.signer)
        initialize(self.path, self.scope, self.pub)

    def e(self, op=None, before_seq=0, before_mac=GENESIS_MAC, after_mac=None):
        return event(self.scope, op or secrets.token_hex(16), before_seq, before_mac,
                     after_mac or secrets.token_hex(32))

    def run_child(self, e, failpoint="", gate=None):
        private = self.signer.private_bytes(encoding=serialization.Encoding.Raw,
                                            format=serialization.PrivateFormat.Raw,
                                            encryption_algorithm=serialization.NoEncryption())
        wire = json.dumps({"test_private_b64": base64.b64encode(private).decode(), "event": e})
        args = [sys.executable, "-m", "tools.imaging_gateway.durable_cas_lab", "--lab-child", "--db", str(self.path)]
        if failpoint:
            args.extend(["--failpoint", failpoint])
        if gate is not None:
            args.extend(["--gate", str(gate)])
        proc = subprocess.run(args, input=wire, text=True, capture_output=True, timeout=20)
        return proc.returncode, proc.stdout, proc.stderr

    def test_signed_receipt_and_one_durable_ledger_row(self):
        e = self.e()
        receipt = apply(self.path, e, self.signer)
        b = verify_receipt(receipt, self.pub)
        self.assertEqual(b["decision"], "ACCEPTED_LAB_NOT_CLINICAL")
        self.assertEqual(b["op_id"], e["op_id"])
        self.assertEqual(audit(self.path, self.scope, self.pub), (1, e["after_mac"], 1))
        self.assertEqual(lookup(self.path, self.scope, e["op_id"], self.pub), receipt)

    def test_same_id_identical_request_replay_returns_exact_saved_receipt(self):
        e = self.e()
        first = apply(self.path, e, self.signer)
        for _ in range(3):
            self.assertEqual(apply(self.path, dict(e), self.signer), first)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 1)

    def test_identical_replay_after_later_accepted_event(self):
        first = self.e()
        receipt = apply(self.path, first, self.signer)
        follow = self.e(before_seq=1, before_mac=first["after_mac"])
        apply(self.path, follow, self.signer)
        self.assertEqual(apply(self.path, first, self.signer), receipt)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 2)

    def test_same_op_id_changed_bytes_always_refused(self):
        e = self.e()
        apply(self.path, e, self.signer)
        altered = {**e, "manifest_digest": "f" * 64}
        with self.assertRaisesRegex(CasRefusal, "OP_ID_REBIND_REFUSE"):
            apply(self.path, altered, self.signer)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 1)

    def test_same_parent_other_operation_fork_refused(self):
        initial = self.e()
        other = self.e()
        apply(self.path, initial, self.signer)
        with self.assertRaisesRegex(CasRefusal, "STALE_OR_FORK_REFUSE"):
            apply(self.path, other, self.signer)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 1)

    def test_wrong_signer_scope_or_existing_epoch_reenroll_refused(self):
        with self.assertRaisesRegex(CasRefusal, "WITNESS_ALREADY_EXISTS"):
            initialize(self.path, self.scope, self.pub)
        with self.assertRaisesRegex(CasRefusal, "UNKNOWN_SCOPE_OR_SIGNER_REFUSE"):
            apply(self.path, self.e(), Ed25519PrivateKey.generate())
        with self.assertRaisesRegex(CasRefusal, "UNKNOWN_SCOPE_OR_SIGNER_REFUSE"):
            apply(self.path, {**self.e(), "scope": secrets.token_hex(16)}, self.signer)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 0)

    def test_reject_schema_patient_fields_noncanon_and_malformed_sequence(self):
        e = self.e()
        with self.assertRaises(CasRefusal):
            event_bytes({**e, "patient_id": "NEVER"})
        with self.assertRaises(CasRefusal):
            event_bytes({**e, "after_seq": 12})
        with self.assertRaises(CasRefusal):
            event_bytes({**e, "before_seq": True})
        with self.assertRaises(CasRefusal):
            event_bytes({**e, "scope": "patient-name"})
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 0)

    def test_missing_database_no_implicit_creation(self):
        self.path.unlink()
        with self.assertRaises(sqlite3.OperationalError):
            apply(self.path, self.e(), self.signer)
        self.assertFalse(self.path.exists())

    def test_wrong_public_pin_refused_and_modified_receipt_detected(self):
        e = self.e()
        receipt = apply(self.path, e, self.signer)
        with self.assertRaises(CasRefusal):
            verify_receipt(receipt, signer_pub(Ed25519PrivateKey.generate()))
        p = json.loads(receipt)
        p["signature_b64"] = base64.b64encode(bytes(64)).decode()
        with self.assertRaises(CasRefusal):
            verify_receipt(canonical(p), self.pub)
        with self.assertRaises(CasRefusal):
            audit(self.path, self.scope, signer_pub(Ed25519PrivateKey.generate()))

    def test_corrupt_ledger_receipt_refused_audit_and_query(self):
        e = self.e()
        apply(self.path, e, self.signer)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE decisions SET receipt_bytes=?", (b"{}",))
        with self.assertRaises(CasRefusal):
            lookup(self.path, self.scope, e["op_id"], self.pub)
        with self.assertRaises(CasRefusal):
            audit(self.path, self.scope, self.pub)

    def test_torn_ledger_head_detected(self):
        e = self.e()
        apply(self.path, e, self.signer)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE authority_head SET seq=100")
        with self.assertRaisesRegex(CasRefusal, "HEAD_LEDGER_DIVERGENCE"):
            audit(self.path, self.scope, self.pub)

    def test_dual_process_one_parent_exactly_one_winner(self):
        gate = Path(self.temp.name) / "go"
        e1,e2 = self.e(),self.e()
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(self.run_child, e1, "", gate)
            f2 = pool.submit(self.run_child, e2, "", gate)
            deadline = time.monotonic() + 10
            while len(list(gate.parent.glob("ready-*"))) < 2 and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertEqual(len(list(gate.parent.glob("ready-*"))), 2, "Both processes must reach barrier")
            gate.touch()
            outcomes = [f1.result(timeout=25),f2.result(timeout=25)]
        self.assertEqual([p[0] for p in outcomes],[0,0],outcomes)
        messages = [json.loads(p[1]) for p in outcomes]
        self.assertEqual(sorted(p["status"] for p in messages), ["DECIDED_LAB_ONLY", "REFUSED"])
        self.assertEqual([p["reason"] for p in messages if p["status"] == "REFUSED"], ["STALE_OR_FORK_REFUSE"])
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 1)

    def test_dual_process_same_op_idempotent_same_receipt_bytes(self):
        gate = Path(self.temp.name) / "go"
        e = self.e()
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(self.run_child, e, "", gate)
            f2 = pool.submit(self.run_child, e, "", gate)
            deadline = time.monotonic() + 10
            while len(list(gate.parent.glob("ready-*"))) < 2 and time.monotonic() < deadline:
                time.sleep(.01)
            self.assertEqual(len(list(gate.parent.glob("ready-*"))), 2, "Both processes must reach barrier")
            gate.touch()
            outcomes = [f1.result(timeout=25),f2.result(timeout=25)]
        self.assertEqual([r[0] for r in outcomes], [0, 0],outcomes)
        messages = [json.loads(r[1]) for r in outcomes]
        self.assertTrue(all(m["status"] == "DECIDED_LAB_ONLY" for m in messages))
        self.assertEqual(messages[0]["receipt_b64"],messages[1]["receipt_b64"])
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 1)

    def test_process_death_before_sqlite_commit_discards_entire_decision(self):
        e = self.e()
        code,out,err = self.run_child(e,"before_commit")
        self.assertEqual(code,86,(out,err))
        self.assertEqual(out, "")
        self.assertIsNone(lookup(self.path,self.scope,e["op_id"],self.pub))
        self.assertEqual(audit(self.path, self.scope, self.pub),(0,GENESIS_MAC,0))
        apply(self.path,e,self.signer)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2],1)

    def test_process_death_after_commit_lost_ack_and_restart_rejoin(self):
        e = self.e()
        code,out,err = self.run_child(e,"after_commit")
        self.assertEqual(code,87,(out,err))
        self.assertEqual(out, "")  # User did not receive ACK, but durable ledger has decision.
        self.assertEqual(audit(self.path, self.scope, self.pub)[2],1)
        persisted = lookup(self.path,self.scope,e["op_id"],self.pub)
        self.assertIsNotNone(persisted)
        self.assertEqual(apply(self.path,e,self.signer),persisted)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2],1)

    def test_reopen_persistent_bytes_and_query_without_private_signer(self):
        e = self.e()
        r = apply(self.path,e,self.signer)
        self.signer = None   # Simulate witness read-only after loss of volatile lab signing key.
        self.assertEqual(lookup(self.path,self.scope,e["op_id"],self.pub),r)
        self.assertEqual(audit(self.path, self.scope, self.pub)[2],1)

    def test_signing_failure_leaves_no_decision_or_advanced_head(self):
        class BrokenSigner:
            def __init__(self, inner): self.inner = inner
            def public_key(self): return self.inner.public_key()
            def sign(self, message): raise RuntimeError("SYNTHETIC_SIGNER_FAILED")
        with self.assertRaisesRegex(RuntimeError, "SYNTHETIC_SIGNER_FAILED"):
            apply(self.path, self.e(), BrokenSigner(self.signer))
        self.assertEqual(audit(self.path, self.scope, self.pub), (0, GENESIS_MAC, 0))

    def test_writer_refuses_to_extend_tampered_existing_head_or_ledger(self):
        e = self.e()
        apply(self.path, e, self.signer)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE decisions SET request_bytes=?", (b"{}",))
        follow = self.e(before_seq=1, before_mac=e["after_mac"])
        with self.assertRaises(CasRefusal):
            apply(self.path, follow, self.signer)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], 1)

    def test_zero_width_schema_and_bad_enrollment_refused(self):
        with self.assertRaises(CasRefusal):
            initialize(Path(self.temp.name) / "another.db", self.scope, b"invalid")
        with self.assertRaises(CasRefusal):
            event_bytes({**self.e(), "key_id": "not-a-valid-key"})
        self.assertEqual(audit(self.path, self.scope, self.pub)[2], 0)

    def test_historical_receipt_is_not_fresh_authorization(self):
        first = self.e()
        historic_receipt = apply(self.path, first, self.signer)
        second = self.e(before_seq=1, before_mac=first["after_mac"])
        apply(self.path, second, self.signer)
        self.assertEqual(lookup(self.path, self.scope, first["op_id"], self.pub), historic_receipt)
        body = verify_receipt(historic_receipt, self.pub)
        self.assertNotEqual(body["after_seq"], audit(self.path, self.scope, self.pub)[0])
        # Correct behavior: historical-only; never a clinical/local-finalize authorization.

    def test_lab_path_rejects_non_disposable_or_symlinked_database(self):
        with self.assertRaisesRegex(CasRefusal, "NON_DISPOSABLE_LAB_PATH_REFUSE"):
            initialize(Path(self.temp.name) / "clinical.sqlite", self.scope, self.pub)
        other_dir = Path(self.temp.name).parent / "not-dc06m-lab"
        with self.assertRaisesRegex(CasRefusal, "NON_DISPOSABLE_LAB_PATH_REFUSE"):
            initialize(other_dir / "witness-synthetic.sqlite", self.scope, self.pub)
        link = Path(self.temp.name) / "unused-symlink"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(CasRefusal, "NON_DISPOSABLE_LAB_PATH_REFUSE"):
            initialize(link, self.scope, self.pub)

    def test_noncanonical_or_malformed_ledger_cannot_be_extended(self):
        first = self.e()
        apply(self.path, first, self.signer)
        follow = self.e(before_seq=1, before_mac=first["after_mac"])
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE decisions SET request_bytes=?", (b'not-json',))
        with self.assertRaisesRegex(CasRefusal, "LEDGER_EVENT_REFUSE"):
            apply(self.path, follow, self.signer)
        with sqlite3.connect(self.path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], 1)

    def test_closed_reader_handles_tampered_signed_decision(self):
        original = self.e()
        apply(self.path, original, self.signer)
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE decisions SET receipt_bytes=?", (b'{"x":"y"}',))
        with self.assertRaises(CasRefusal):
            lookup(self.path, self.scope, original["op_id"], self.pub)
        with self.assertRaises(CasRefusal):
            audit(self.path, self.scope, self.pub)

    def test_old_database_plus_old_anchor_replay_still_passes_lab_audit(self):
        # Important negative proof: same-machine SQLite cannot detect cross-domain rollback.
        e1 = self.e()
        apply(self.path,e1,self.signer)
        old = Path(self.temp.name)/"old_backup.db"
        shutil.copy2(self.path,old)
        e2 = self.e(before_seq=1,before_mac=e1["after_mac"])
        apply(self.path,e2,self.signer)
        self.assertEqual(audit(self.path,self.scope,self.pub)[2],2)
        shutil.copy2(old,self.path)
        self.assertEqual(audit(self.path,self.scope,self.pub)[2],1)  # Pinned signer + old state accepted!
        self.assertIsNone(lookup(self.path,self.scope,e2["op_id"],self.pub))


if __name__ == "__main__":
    unittest.main()
