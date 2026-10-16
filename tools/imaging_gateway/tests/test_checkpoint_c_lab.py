"""LOT06-N B9 synthetic C-checkpoint experiments; no physical trust domain."""
from __future__ import annotations

import hashlib
from pathlib import Path
import secrets
import shutil
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.imaging_gateway.checkpoint_c_lab import (
    SyntheticCheckpointC, classify_verified_head, verify_anchor,
)
from tools.imaging_gateway.durable_cas_lab import (
    AUTHORITY, EPOCH, GENESIS_MAC, CasRefusal, apply, audit, canonical, event, initialize,
    signer_pub,
)
from tools.imaging_gateway.independent_witness_lab import (
    b64, proof_bytes, verify_response,
)


class CheckpointCSyntheticTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="dc06m-cas-synthetic-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = self.root / "witness-synthetic.sqlite"
        self.scope = secrets.token_hex(16)
        self.b_key = Ed25519PrivateKey.generate()
        self.c_key = Ed25519PrivateKey.generate()
        self.b_pin, self.c_pin = signer_pub(self.b_key), signer_pub(self.c_key)
        initialize(self.db, self.scope, self.b_pin)
        self.c = SyntheticCheckpointC(self.scope, self.b_pin, self.c_key)

    def commit_b(self, seq=0, mac=GENESIS_MAC, op=None):
        e = event(self.scope, op or secrets.token_hex(16), seq, mac,
                  secrets.token_hex(32))
        receipt = apply(self.db, e, self.b_key)
        return e, receipt

    def fresh_head(self, *, seq=None, mac=None):
        # This is signed by the same harness-owned B key, NOT a physical attestor.
        actual_seq, actual_mac, _ = audit(self.db, self.scope, self.b_pin)
        seq = actual_seq if seq is None else seq
        mac = actual_mac if mac is None else mac
        req = {"protocol": "DC06N_SYNTHETIC_V1", "method": "HEAD",
               "scope": self.scope, "challenge": secrets.token_hex(16),
               "op_id": secrets.token_hex(16), "event": None}
        proof = {"protocol": "DC06N_SYNTHETIC_V1", "authority_id": AUTHORITY,
                 "epoch": EPOCH, "scope": self.scope, "challenge": req["challenge"],
                 "method": "HEAD", "op_id": req["op_id"], "seq": seq, "mac": mac,
                 "status": "HEAD_ONLY", "receipt_b64": ""}
        packet = {"proof": proof, "signature_b64": b64(self.b_key.sign(proof_bytes(proof)))}
        self.assertEqual(verify_response(packet, self.b_pin, req)["status"], "HEAD_ONLY")
        return packet, req

    def verdict(self, c_packet=None, head=None):
        witness_packet, req = head or self.fresh_head()
        return classify_verified_head(witness_packet, req,
                                      self.c.latest if c_packet is None else c_packet,
                                      self.b_pin, self.c_pin)

    def test_genesis_anchor_signed_but_not_real_freshness(self):
        proof = verify_anchor(self.c.latest, self.c_pin, self.b_pin, self.scope)
        self.assertEqual(proof["seq"], 0)
        self.assertEqual(self.verdict().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_pending_c_when_b_advanced_without_anchor(self):
        self.commit_b()
        result = self.verdict()
        self.assertEqual(result.status, "PENDING_C_ANCHOR_LAB")
        self.assertEqual((result.witness_seq, result.checkpoint_seq), (1, 0))

    def test_sequential_anchor_and_exact_idempotent_replay(self):
        e, receipt = self.commit_b()
        one = self.c.anchor(receipt)
        self.assertEqual(self.c.anchor(receipt), one)
        self.assertEqual(self.verdict().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")
        e2, receipt2 = self.commit_b(1, e["after_mac"])
        two = self.c.anchor(receipt2)
        self.assertEqual(two["checkpoint"]["seq"], 2)
        self.assertEqual(two["checkpoint"]["prev_checkpoint_sha256"],
                         hashlib.sha256(canonical(one)).hexdigest())
        self.assertEqual(self.verdict().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_gap_or_fork_in_anchor_refused(self):
        first, r1 = self.commit_b()
        _, r2 = self.commit_b(1, first["after_mac"])
        with self.assertRaisesRegex(CasRefusal, "C_STALE_FORK_OR_GAP_REFUSE"):
            self.c.anchor(r2)
        self.c.anchor(r1)
        self.c.anchor(r2)
        self.assertEqual(self.c.anchor(r2), self.c.anchor(r2))

    def test_missing_c_or_head_never_means_decided(self):
        head = self.fresh_head()
        self.assertEqual(classify_verified_head(head[0], head[1], None,
                         self.b_pin, self.c_pin).status,
                         "UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB")
        self.assertEqual(classify_verified_head(None, head[1], self.c.latest,
                         self.b_pin, self.c_pin).status,
                         "UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB")

    def test_wrong_c_key_or_tampered_checkpoint_refused(self):
        e, r1 = self.commit_b()
        anchor = self.c.anchor(r1)
        with self.assertRaisesRegex(CasRefusal, "C_SIGNATURE_REFUSE"):
            verify_anchor(anchor, signer_pub(Ed25519PrivateKey.generate()),
                          self.b_pin, self.scope)
        forged = {"checkpoint": {**anchor["checkpoint"], "seq": 0},
                  "signature_b64": anchor["signature_b64"]}
        with self.assertRaisesRegex(CasRefusal, "C_SIGNATURE_REFUSE"):
            verify_anchor(forged, self.c_pin, self.b_pin, self.scope)
        with self.assertRaisesRegex(CasRefusal, "C_ANCHOR_BINDING_REFUSE"):
            verify_anchor(anchor, self.c_pin, signer_pub(Ed25519PrivateKey.generate()),
                          self.scope)

    def test_bad_witness_receipt_cannot_be_anchored(self):
        _, r = self.commit_b()
        with self.assertRaises(CasRefusal):
            self.c.anchor(r[:-1] + b"X")
        self.assertEqual(self.c.latest["checkpoint"]["seq"], 0)

    def test_forged_witness_head_or_replayed_challenge_refused(self):
        self.c.anchor(self.commit_b()[1])
        pkt, req = self.fresh_head()
        fake = {"proof": {**pkt["proof"], "seq": 0}, "signature_b64": pkt["signature_b64"]}
        with self.assertRaisesRegex(CasRefusal, "RESPONSE_SIGNATURE_REFUSE"):
            classify_verified_head(fake, req, self.c.latest, self.b_pin, self.c_pin)
        reused = {**req, "challenge": secrets.token_hex(16)}
        with self.assertRaisesRegex(CasRefusal, "RESPONSE_BINDING_REFUSE"):
            classify_verified_head(pkt, reused, self.c.latest, self.b_pin, self.c_pin)

    def test_b_rollback_old_sqlite_and_same_signer_c_intact_refuses(self):
        one, r1 = self.commit_b()
        historical_c = self.c.anchor(r1)
        backup = self.root / "old-b.db"
        shutil.copy2(self.db, backup)
        _, r2 = self.commit_b(1, one["after_mac"])
        self.c.anchor(r2)
        self.assertEqual(self.verdict().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")
        # B may be rolled back along with its valid signer: fresh signed old HEAD!
        shutil.copy2(backup, self.db)
        signed_rolled_back_head = self.fresh_head()
        self.assertEqual(self.verdict(head=signed_rolled_back_head).status,
                         "B_ROLLBACK_DETECTED_LAB")
        self.assertEqual(self.verdict(head=signed_rolled_back_head).checkpoint_seq, 2)
        # An older, authentic C packet is insufficient to prove the CURRENT C head.
        self.assertEqual(self.verdict(c_packet=historical_c,
                                     head=signed_rolled_back_head).status,
                         "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_rollback_b_and_c_together_remains_undetectable_in_lab(self):
        first, r1 = self.commit_b()
        old_c = self.c.anchor(r1)
        backup = self.root / "old-b.db"
        shutil.copy2(self.db, backup)
        _, r2 = self.commit_b(1, first["after_mac"])
        self.c.anchor(r2)
        shutil.copy2(backup, self.db)
        # Model of an attacker who also replays an old genuine C signed packet.
        # This is a PROVEN LIMITATION: never turn MATCH into a clinical guarantee.
        self.assertEqual(self.verdict(c_packet=old_c).status,
                         "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_same_sequence_different_head_classified_fork(self):
        _, r1 = self.commit_b()
        self.c.anchor(r1)
        fake_b_head = self.fresh_head(mac=secrets.token_hex(32))
        self.assertEqual(self.verdict(head=fake_b_head).status,
                         "SAME_SEQ_FORK_REFUSED_LAB")

    def test_caller_cannot_mutate_in_memory_c_history_through_return_value(self):
        first, r1 = self.commit_b()
        exposed = self.c.anchor(r1)
        exposed["checkpoint"]["mac"] = "f" * 64
        exposed["signature_b64"] = "CORRUPTED"
        replay = self.c.anchor(r1)
        self.assertEqual(replay["checkpoint"]["mac"], first["after_mac"])
        verify_anchor(replay, self.c_pin, self.b_pin, self.scope)
        _, r2 = self.commit_b(1, first["after_mac"])
        anchored = self.c.anchor(r2)
        self.assertEqual(anchored["checkpoint"]["seq"], 2)
        self.assertEqual(self.verdict().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_malformed_head_request_refuses_not_crashes(self):
        with self.assertRaisesRegex(CasRefusal, "C_EXPECT_HEAD_REFUSE"):
            classify_verified_head(None, None, None, self.b_pin, self.c_pin)

    def test_scope_mismatch_is_refused(self):
        _, r1 = self.commit_b()
        anchor = self.c.anchor(r1)
        with self.assertRaisesRegex(CasRefusal, "C_ANCHOR_BINDING_REFUSE"):
            verify_anchor(anchor, self.c_pin, self.b_pin, secrets.token_hex(16))


if __name__ == "__main__":
    unittest.main()
