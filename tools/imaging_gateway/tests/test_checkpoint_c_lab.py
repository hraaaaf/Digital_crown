"""LOT06-N B9 synthetic C-checkpoint experiments; no physical trust domain."""
from __future__ import annotations

import hashlib
from pathlib import Path
import secrets
import shutil
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from tools.imaging_gateway.checkpoint_c_lab import (
    SyntheticCheckpointC, classify_verified_head, classify_challenged_heads,
    reconcile_challenged_receipt, verify_anchor, verify_challenged_c_head,
)
from tools.imaging_gateway.durable_cas_lab import (
    AUTHORITY, EPOCH, GENESIS_MAC, CasRefusal, apply, audit, canonical, event, initialize,
    lookup, signer_pub, verify_receipt,
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

    def test_c_signer_failure_never_advances_anchor_head(self):
        e, receipt = self.commit_b()
        with patch.object(self.c, "_sign", side_effect=CasRefusal("C_SIGN_FAILED_LAB")):
            with self.assertRaisesRegex(CasRefusal, "C_SIGN_FAILED_LAB"):
                self.c.anchor(receipt)
        self.assertEqual(self.c.latest["checkpoint"]["seq"], 0)
        self.assertEqual(self.verdict().status, "PENDING_C_ANCHOR_LAB")
        self.assertEqual(self.c.anchor(receipt)["checkpoint"]["seq"], 1)
        self.assertEqual(self.verdict().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def dual(self, *, c=None, b=None, challenge=None):
        b_pkt, b_req = b if b is not None else self.fresh_head()
        nonce = challenge or secrets.token_hex(16)
        c_pkt = self.c.challenged_head(nonce) if c is None else c
        return classify_challenged_heads(
            b_pkt, b_req, c_pkt, nonce, self.b_pin, self.c_pin)

    def test_challenged_c_genesis_match_is_not_authorization(self):
        self.assertEqual(self.dual().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_challenged_c_b_ahead_pending_before_anchor(self):
        _, receipt = self.commit_b()
        self.assertEqual(self.dual().status, "PENDING_C_ANCHOR_LAB")
        self.c.anchor(receipt)
        self.assertEqual(self.dual().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_challenged_c_new_nonce_rejects_replay_of_old_signed_head(self):
        old_nonce = secrets.token_hex(16)
        old_head = self.c.challenged_head(old_nonce)
        with self.assertRaisesRegex(CasRefusal, "C_HEAD_CHALLENGE_BINDING_REFUSE"):
            self.dual(c=old_head, challenge=secrets.token_hex(16))
        self.assertEqual(self.dual(c=old_head, challenge=old_nonce).status,
                         "MATCH_LAB_NOT_GLOBAL_FRESHNESS")

    def test_challenged_c_tamper_or_wrong_pin_fails_closed(self):
        nonce = secrets.token_hex(16)
        old_head = self.c.challenged_head(nonce)
        bad = {"response": {**old_head["response"], "protocol": "BAD_PROTOCOL"},
               "signature_b64": old_head["signature_b64"]}
        with self.assertRaisesRegex(CasRefusal, "C_HEAD_CHALLENGE_BINDING_REFUSE"):
            self.dual(c=bad, challenge=nonce)
        tampered = {"response": {**old_head["response"],
                    "anchor": {**old_head["response"]["anchor"],
                              "checkpoint": {**old_head["response"]["anchor"]["checkpoint"],
                                             "seq": 1}}},
                    "signature_b64": old_head["signature_b64"]}
        with self.assertRaisesRegex(CasRefusal, "C_HEAD_SIGNATURE_REFUSE"):
            self.dual(c=tampered, challenge=nonce)
        with self.assertRaisesRegex(CasRefusal, "C_HEAD_SIGNATURE_REFUSE"):
            verify_challenged_c_head(old_head, nonce,
                                     signer_pub(Ed25519PrivateKey.generate()),
                                     self.b_pin, self.scope)

    def test_challenged_c_missing_either_side_unknown(self):
        b_pkt, b_req = self.fresh_head()
        nonce = secrets.token_hex(16)
        c_pkt = self.c.challenged_head(nonce)
        self.assertEqual(classify_challenged_heads(
            b_pkt, b_req, None, nonce, self.b_pin, self.c_pin).status,
            "UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB")
        self.assertEqual(classify_challenged_heads(
            None, b_req, c_pkt, nonce, self.b_pin, self.c_pin).status,
            "UNKNOWN_NO_INDEPENDENT_CURRENT_C_LAB")

    def test_challenged_c_detects_b_rollback_if_c_current(self):
        first, r1 = self.commit_b()
        self.c.anchor(r1)
        saved = self.root / "saved-b-for-challenged.db"
        shutil.copy2(self.db, saved)
        _, r2 = self.commit_b(1, first["after_mac"])
        self.c.anchor(r2)
        shutil.copy2(saved, self.db)
        self.assertEqual(self.dual().status, "B_ROLLBACK_DETECTED_LAB")

    def test_restored_c_can_freshly_sign_old_state_no_physical_proof(self):
        first, r1 = self.commit_b()
        older_c = SyntheticCheckpointC(self.scope, self.b_pin, self.c_key)
        older_c.anchor(r1)
        self.c.anchor(r1)
        saved = self.root / "saved-b-and-c.db"
        shutil.copy2(self.db, saved)
        _, r2 = self.commit_b(1, first["after_mac"])
        self.c.anchor(r2)
        shutil.copy2(saved, self.db)
        # This C shares the old (valid) key and state, yet signs the NEW
        # challenge; nonce freshness is NOT monotonic rollback protection.
        nonce = secrets.token_hex(16)
        fresh_from_stale_c = older_c.challenged_head(nonce)
        self.assertEqual(self.dual(c=fresh_from_stale_c, challenge=nonce).status,
                         "MATCH_LAB_NOT_GLOBAL_FRESHNESS")
        self.assertEqual(self.dual().status, "B_ROLLBACK_DETECTED_LAB")

    def test_challenged_c_rejects_malformed_structure_or_challenge(self):
        nonce = secrets.token_hex(16)
        with self.assertRaisesRegex(CasRefusal, "C_HEAD_CHALLENGE_SHAPE_REFUSE"):
            self.c.challenged_head("bad")
        with self.assertRaisesRegex(CasRefusal, "C_HEAD_PACKET_SHAPE_REFUSE"):
            verify_challenged_c_head({}, nonce, self.c_pin, self.b_pin, self.scope)
        b_pkt, b_req = self.fresh_head()
        with self.assertRaisesRegex(CasRefusal, "C_DUAL_CHALLENGE_REFUSE"):
            classify_challenged_heads(b_pkt, b_req, None, "wrong",
                                     self.b_pin, self.c_pin)

    def signed_lookup(self, op_id):
        seq, mac, _ = audit(self.db, self.scope, self.b_pin)
        raw = lookup(self.db, self.scope, op_id, self.b_pin)
        if raw is None:
            status = "UNKNOWN_OP"
        elif verify_receipt(raw, self.b_pin)["after_seq"] == seq:
            status = "DECIDED_LAB_ONLY"
        else:
            status = "HISTORICAL_ONLY"
        req = {"protocol": "DC06N_SYNTHETIC_V1", "method": "LOOKUP",
               "scope": self.scope, "challenge": secrets.token_hex(16),
               "op_id": op_id, "event": None}
        proof = {"protocol": "DC06N_SYNTHETIC_V1", "authority_id": AUTHORITY,
                 "epoch": EPOCH, "scope": self.scope, "challenge": req["challenge"],
                 "method": "LOOKUP", "op_id": op_id, "seq": seq, "mac": mac,
                 "status": status, "receipt_b64": b64(raw) if raw else ""}
        packet = {"proof": proof, "signature_b64": b64(
            self.b_key.sign(proof_bytes(proof)))}
        self.assertEqual(verify_response(packet, self.b_pin, req)["status"], status)
        return packet, req

    def receipts(self, op_id, *, head=None, lookup_pair=None):
        b_packet, b_req = head or self.fresh_head()
        nonce = secrets.token_hex(16)
        c_packet = self.c.challenged_head(nonce)
        lookup_packet, lookup_req = lookup_pair or self.signed_lookup(op_id)
        return reconcile_challenged_receipt(
            b_packet, b_req, c_packet, nonce, lookup_packet, lookup_req,
            self.b_pin, self.c_pin)

    def test_receipt_reconcile_genesis_without_fabricated_receipt(self):
        b_packet, b_req = self.fresh_head()
        nonce = secrets.token_hex(16)
        result = reconcile_challenged_receipt(
            b_packet, b_req, self.c.challenged_head(nonce), nonce,
            None, None, self.b_pin, self.c_pin)
        self.assertEqual(result.status, "MATCH_GENESIS_LAB_NOT_AUTHORITY")

    def test_receipt_reconcile_exact_B_lookup_with_C_hash(self):
        e, r1 = self.commit_b()
        self.c.anchor(r1)
        result = self.receipts(e["op_id"])
        self.assertEqual(result.status, "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")
        self.assertEqual((result.witness_seq, result.checkpoint_seq), (1, 1))

    def test_receipt_reconcile_missing_B_lookup_never_match(self):
        e, r1 = self.commit_b()
        self.c.anchor(r1)
        b_pkt, b_req = self.fresh_head()
        nonce = secrets.token_hex(16)
        result = reconcile_challenged_receipt(
            b_pkt, b_req, self.c.challenged_head(nonce), nonce,
            None, None, self.b_pin, self.c_pin)
        self.assertEqual(result.status, "UNKNOWN_B_CURRENT_RECEIPT_LAB")

    def test_receipt_reconcile_B_ahead_not_claim_anchored(self):
        e, r1 = self.commit_b()
        self.assertEqual(self.receipts(e["op_id"]).status,
                         "PENDING_C_ANCHOR_LAB")

    def test_receipt_reconcile_historical_lookup_is_conflict(self):
        first, r1 = self.commit_b()
        self.c.anchor(r1)
        old_head = self.fresh_head()
        self.commit_b(1, first["after_mac"])
        result = self.receipts(first["op_id"], head=old_head)
        self.assertEqual(result.status, "B_RECEIPT_HEAD_CONFLICT_LAB")

    def test_receipt_reconcile_same_head_but_changed_signed_receipt_refuses(self):
        genesis = self.root / "genesis-receipt-rebind.db"
        shutil.copy2(self.db, genesis)
        first, r1 = self.commit_b()
        self.c.anchor(r1)
        # Adversarial restore and re-sign: SAME seq/mac/op_id, but a
        # DIFFERENT manifest, canonical proposal and signed receipt.
        shutil.copy2(genesis, self.db)
        changed = {**first, "manifest_digest": "f" * 64}
        r2 = apply(self.db, changed, self.b_key)
        self.assertNotEqual(r1, r2)
        self.assertEqual(self.dual().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")
        self.assertEqual(self.receipts(first["op_id"]).status,
                         "B_C_RECEIPT_HASH_CONFLICT_LAB")

    def test_receipt_reconcile_missing_op_after_rollback_is_unknown(self):
        genesis = self.root / "genesis-missing-op.db"
        shutil.copy2(self.db, genesis)
        first, r1 = self.commit_b()
        self.c.anchor(r1)
        shutil.copy2(genesis, self.db)
        changed = event(self.scope, secrets.token_hex(16), 0, GENESIS_MAC,
                        first["after_mac"])
        apply(self.db, changed, self.b_key)
        self.assertEqual(self.dual().status, "MATCH_LAB_NOT_GLOBAL_FRESHNESS")
        self.assertEqual(self.receipts(first["op_id"]).status,
                         "UNKNOWN_B_CURRENT_RECEIPT_LAB")

    def test_receipt_reconcile_tampered_signed_lookup_refused(self):
        first, r1 = self.commit_b()
        self.c.anchor(r1)
        lookup_pkt, lookup_req = self.signed_lookup(first["op_id"])
        corrupted = {"proof": {**lookup_pkt["proof"], "receipt_b64": "AA=="},
                     "signature_b64": lookup_pkt["signature_b64"]}
        with self.assertRaisesRegex(CasRefusal, "RESPONSE_SIGNATURE_REFUSE"):
            self.receipts(first["op_id"], lookup_pair=(corrupted, lookup_req))

    def test_receipt_reconcile_wrong_lookup_op_refused(self):
        first, r1 = self.commit_b()
        self.c.anchor(r1)
        lookup_pkt, lookup_req = self.signed_lookup(first["op_id"])
        wrong_req = {**lookup_req, "op_id": secrets.token_hex(16)}
        with self.assertRaisesRegex(CasRefusal, "B_RECEIPT_LOOKUP_OP_REFUSE"):
            self.receipts(first["op_id"], lookup_pair=(lookup_pkt, wrong_req))

    def test_B_and_C_same_signer_identity_refused_even_in_synthetic_lab(self):
        with self.assertRaisesRegex(CasRefusal, "C_B_SAME_SIGNER_REFUSE"):
            SyntheticCheckpointC(self.scope, self.b_pin, self.b_key)
        with self.assertRaisesRegex(CasRefusal, "C_B_SAME_SIGNER_REFUSE"):
            verify_anchor(self.c.latest, self.b_pin, self.b_pin, self.scope)

    def test_scope_mismatch_is_refused(self):
        _, r1 = self.commit_b()
        anchor = self.c.anchor(r1)
        with self.assertRaisesRegex(CasRefusal, "C_ANCHOR_BINDING_REFUSE"):
            verify_anchor(anchor, self.c_pin, self.b_pin, secrets.token_hex(16))


if __name__ == "__main__":
    unittest.main()
