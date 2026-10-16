"""LOT06-N synthetic-only adversarial/property-stress battery.

No physical devices, real workstations, site data, removable storage, network
outside a disposable CI process, or clinical authorization. Deterministic tests
run on the same ephemeral fixtures as test_checkpoint_c_lab.py.
"""
from __future__ import annotations

import base64
from copy import deepcopy
import secrets
import shutil
import sqlite3
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import test_checkpoint_c_lab as fixture_module

from tools.imaging_gateway.checkpoint_c_lab import (
    SyntheticCheckpointC, classify_challenged_heads,
    reconcile_challenged_receipt, verify_anchor, verify_challenged_c_head,
)
from tools.imaging_gateway.durable_cas_lab import (
    AUTHORITY, EPOCH, GENESIS_MAC, CasRefusal, _receipt, audit, event,
    event_bytes, signer_pub, verify_receipt,
)
from tools.imaging_gateway.independent_witness_lab import b64, proof_bytes


class CheckpointCAdversarialSynthetic(unittest.TestCase):
    def setUp(self):
        # Reuse the original test fixture without inheriting its 33 test methods.
        self.lab = fixture_module.CheckpointCSyntheticTests(
            "test_genesis_anchor_signed_but_not_real_freshness")
        self.lab.setUp()
        self.addCleanup(self.lab.doCleanups)

    def _exchange(self, *, head=None, c=None, nonce=None, lookup_pair=None):
        l = self.lab
        b_head, b_req = head if head is not None else l.fresh_head()
        nonce = nonce if nonce is not None else secrets.token_hex(16)
        c_packet = c if c is not None else l.c.challenged_head(nonce)
        op = c_packet["response"]["anchor"]["checkpoint"]["op_id"]
        lookup_pkt, lookup_req = (
            lookup_pair if lookup_pair is not None else l.signed_lookup(op))
        return reconcile_challenged_receipt(
            b_head, b_req, c_packet, nonce, lookup_pkt, lookup_req,
            l.b_pin, l.c_pin)

    def test_40_step_head_and_receipt_state_machine(self):
        l = self.lab
        seq, mac = 0, GENESIS_MAC
        history = []
        for index in range(40):
            op = f"{index + 1:032x}"
            e, receipt = l.commit_b(seq, mac, op=op)
            self.assertEqual(verify_receipt(receipt, l.b_pin)["after_seq"], index + 1)
            anchor = l.c.anchor(receipt)
            self.assertEqual(anchor["checkpoint"]["seq"], index + 1)
            self.assertEqual(self._exchange().status,
                             "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")
            history.append((receipt, anchor))
            seq, mac = e["after_seq"], e["after_mac"]
            self.assertEqual(audit(l.db, l.scope, l.b_pin)[0], seq)
        # A replay of any genuinely anchored operation must not roll C back.
        for old_receipt, old_anchor in history[::5]:
            self.assertEqual(l.c.anchor(old_receipt), old_anchor)
            self.assertEqual(l.c.latest["checkpoint"]["seq"], 40)
        self.assertEqual(self._exchange().status,
                         "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")

    def test_20_synthetic_copy_restore_head_differential(self):
        l = self.lab
        first, r1 = l.commit_b()
        l.c.anchor(r1)
        old_db = l.root / "synthetic-checkpoint-copy.db"
        shutil.copy2(l.db, old_db)
        seq, mac = 1, first["after_mac"]
        for index in range(20):
            e, receipt = l.commit_b(seq, mac)
            l.c.anchor(receipt)
            seq, mac = e["after_seq"], e["after_mac"]
        self.assertEqual(self._exchange().status,
                         "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")
        # A synthetic B-only restore cannot be accepted against C's newer head.
        shutil.copy2(old_db, l.db)
        self.assertEqual(l.dual().status, "B_ROLLBACK_DETECTED_LAB")
        self.assertEqual(self._exchange().status, "B_ROLLBACK_DETECTED_LAB")

    def test_c_restored_with_valid_key_still_matches_old_b_full_receipt(self):
        l = self.lab
        first, r1 = l.commit_b()
        l.c.anchor(r1)
        old_c = SyntheticCheckpointC(l.scope, l.b_pin, l.c_key)
        old_c.anchor(r1)
        old_db = l.root / "synthetic-b-and-c-copy.db"
        shutil.copy2(l.db, old_db)
        _, r2 = l.commit_b(1, first["after_mac"])
        l.c.anchor(r2)
        shutil.copy2(old_db, l.db)
        # Both signed proofs and the exact receipt remain self-consistent.
        # This must NEVER be described as a global freshness guarantee.
        nonce = secrets.token_hex(16)
        from_restored_c = old_c.challenged_head(nonce)
        self.assertEqual(self._exchange(c=from_restored_c, nonce=nonce).status,
                         "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")
        self.assertEqual(self._exchange().status,
                         "B_ROLLBACK_DETECTED_LAB")

    def test_signed_lookup_field_mutation_matrix_never_authorizes(self):
        l = self.lab
        e, receipt = l.commit_b()
        l.c.anchor(receipt)
        valid, req = l.signed_lookup(e["op_id"])
        changes = {
            "protocol": "wrong-lab",
            "authority_id": "different-authority",
            "epoch": "OTHER_EPOCH",
            "scope": "e" * 32 if l.scope != "e" * 32 else "d" * 32,
            "challenge": secrets.token_hex(16),
            "method": "HEAD",
            "op_id": secrets.token_hex(16),
            "seq": 0,
            "mac": "e" * 64,
            "status": "HISTORICAL_ONLY",
            "receipt_b64": "",
        }
        for field, changed in changes.items():
            with self.subTest(field=field):
                mutated = {**valid["proof"], field: changed}
                packet = {"proof": mutated,
                          "signature_b64": b64(l.b_key.sign(proof_bytes(mutated)))}
                try:
                    result = self._exchange(lookup_pair=(packet, req))
                except CasRefusal:
                    continue
                self.assertNotEqual(result.status, "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY",
                                    "mutated signed lookup must not authorize")

    def test_challenge_and_key_cross_binding_matrix(self):
        l = self.lab
        e, r = l.commit_b()
        l.c.anchor(r)
        b_head, original_req = l.fresh_head()
        nonce = secrets.token_hex(16)
        c_head = l.c.challenged_head(nonce)
        for kind in ("wrong_nonce", "wrong_c_pin", "wrong_b_pin",
                     "wrong_scope", "truncated_c_signature"):
            with self.subTest(case=kind):
                b_req = dict(original_req)
                c_packet = deepcopy(c_head)
                challenge = nonce
                b_pin = l.b_pin
                c_pin = l.c_pin
                if kind == "wrong_nonce":
                    challenge = secrets.token_hex(16)
                elif kind == "wrong_c_pin":
                    c_pin = signer_pub(Ed25519PrivateKey.generate())
                elif kind == "wrong_b_pin":
                    b_pin = signer_pub(Ed25519PrivateKey.generate())
                elif kind == "wrong_scope":
                    b_req = {**b_req, "scope": secrets.token_hex(16)}
                else:
                    c_packet["signature_b64"] = c_packet["signature_b64"][:40]
                with self.assertRaises(CasRefusal):
                    classify_challenged_heads(b_head, b_req, c_packet,
                                              challenge, b_pin, c_pin)

    def test_signed_anchor_mutation_matrix_rejects_untampered_signature(self):
        l = self.lab
        e, receipt = l.commit_b()
        anchor = l.c.anchor(receipt)
        checkpoint = anchor["checkpoint"]
        changes = {
            "protocol": "OLD",
            "authority_id": "other",
            "epoch": "other",
            "scope": secrets.token_hex(16),
            "witness_pin_sha256": "a" * 64,
            "seq": 2,
            "mac": "a" * 64,
            "op_id": secrets.token_hex(16),
            "receipt_sha256": "a" * 64,
            "prev_checkpoint_sha256": "a" * 64,
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                altered = {"checkpoint": {**checkpoint, field: value},
                           "signature_b64": anchor["signature_b64"]}
                with self.assertRaises(CasRefusal):
                    verify_anchor(altered, l.c_pin, l.b_pin, l.scope)

    def test_validly_signed_receipt_rebind_with_same_op_refused_at_c(self):
        l = self.lab
        original, receipt = l.commit_b()
        l.c.anchor(receipt)
        # A *different but correctly signed* witness receipt under the same
        # op_id cannot replace C's previous bound receipt.
        changed_event = {**original, "manifest_digest": "f" * 64}
        conflicting = _receipt(changed_event, event_bytes(changed_event), l.b_key)
        self.assertNotEqual(conflicting, receipt)
        self.assertEqual(verify_receipt(conflicting, l.b_pin)["op_id"],
                         original["op_id"])
        with self.assertRaisesRegex(CasRefusal, "C_OP_ID_REBIND_REFUSE"):
            l.c.anchor(conflicting)
        self.assertEqual(l.c.latest["checkpoint"]["seq"], 1)
        self.assertEqual(self._exchange().status,
                         "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")

    def test_c_signer_failure_does_not_advance_or_erase_replay(self):
        l = self.lab
        e, receipt = l.commit_b()
        old = l.c.latest
        from unittest.mock import patch
        with patch.object(l.c, "_sign", side_effect=CasRefusal("INJECTED_SIGN_FAIL")):
            with self.assertRaisesRegex(CasRefusal, "INJECTED_SIGN_FAIL"):
                l.c.anchor(receipt)
        self.assertEqual(l.c.latest, old)
        l.c.anchor(receipt)
        self.assertEqual(self._exchange().status,
                         "MATCH_B_C_RECEIPT_LAB_NOT_AUTHORITY")

    def test_signed_lookup_unknown_operation_stays_unknown(self):
        l = self.lab
        e, receipt = l.commit_b()
        l.c.anchor(receipt)
        b_head, b_req = l.fresh_head()
        nonce = secrets.token_hex(16)
        c_packet = l.c.challenged_head(nonce)
        pkt, req = l.signed_lookup(secrets.token_hex(16))
        with self.assertRaisesRegex(CasRefusal, "B_RECEIPT_LOOKUP_OP_REFUSE"):
            reconcile_challenged_receipt(
                b_head, b_req, c_packet, nonce, pkt, req, l.b_pin, l.c_pin)

    def test_same_key_for_B_and_C_rejected_before_signed_envelope(self):
        l = self.lab
        with self.assertRaisesRegex(CasRefusal, "C_B_SAME_SIGNER_REFUSE"):
            SyntheticCheckpointC(l.scope, l.b_pin, l.b_key)

    def test_malformed_c_head_structures_refuse_without_success(self):
        l = self.lab
        nonce = secrets.token_hex(16)
        valid = l.c.challenged_head(nonce)
        mutations = [
            None, [], {}, {"response": {}, "signature_b64": "x"},
            {"response": [], "signature_b64": "x"},
            {"response": {**valid["response"], "challenge": None},
             "signature_b64": valid["signature_b64"]},
            {"response": valid["response"], "signature_b64": None},
            {"response": valid["response"], "signature_b64": "@" * 88},
        ]
        for packet in mutations:
            with self.subTest(shape=str(type(packet)), value=str(packet)[:45]):
                with self.assertRaises(CasRefusal):
                    verify_challenged_c_head(packet, nonce, l.c_pin,
                                             l.b_pin, l.scope)

    def test_different_B_scope_signed_head_refused(self):
        l = self.lab
        b_head, req = l.fresh_head()
        nonce = secrets.token_hex(16)
        req["scope"] = secrets.token_hex(16)
        with self.assertRaises(CasRefusal):
            classify_challenged_heads(
                b_head, req, l.c.challenged_head(nonce), nonce,
                l.b_pin, l.c_pin)


if __name__ == "__main__":
    unittest.main()
