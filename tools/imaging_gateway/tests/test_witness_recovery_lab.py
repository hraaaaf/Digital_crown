"""LOT06-M corrective adversarial LAB: idempotence, lost ACK, archive proof."""
from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import unittest

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tools.imaging_gateway import migration_lab as m
from tools.imaging_gateway import journal_lab as j
from tools.imaging_gateway import fork_lab as f
from tools.imaging_gateway import witness_recovery_lab as w


class DecisionAndRestoreTests(unittest.TestCase):
    def setUp(self):
        self.clear = b"synthetic-lot06-m-only"
        self.legacy_key = b"L"*32
        self.journal_key = b"J"*32
        self.keys = {"ab"*16:b"T"*32, "cd"*16:b"U"*32}
        identity = "e"*64
        nonce=b"synthetic123"
        aad=("DC06A|lab_m|workstation_m|"+identity).encode("ascii")
        source=b"DC6A"+nonce+AESGCM(self.legacy_key).encrypt(
            nonce,self.clear,aad
        )
        self.genesis=m.begin(
            source,cabinet="lab_m",workstation="workstation_m",
            identity=identity,digest=hashlib.sha256(self.clear).hexdigest(),
            legacy_key=self.legacy_key
        )
        self.j0,self.a0=j.initialize(
            self.genesis,journal_key=self.journal_key,
            legacy_key=self.legacy_key,keys=self.keys
        )
        self.witness=w.VolatileDecisionWitness(
            self.j0,self.a0,epoch="e1",opaque_scope="a"*32,
            journal_key=self.journal_key,legacy_key=self.legacy_key,keys=self.keys
        )
        self.op1="1"*32
        self.op2="2"*32

    def proposal(self, kid="ab"*16, base=None, anchor=None, state=None):
        base=self.j0 if base is None else base
        anchor=self.a0 if anchor is None else anchor
        if state is None:
            state=m.prepare(self.genesis,expected_revision=0,
                            legacy_key=self.legacy_key,target_key_id=kid,
                            keys=self.keys)
        return f.propose(base,anchor,state,journal_key=self.journal_key,
                         legacy_key=self.legacy_key,keys=self.keys)

    def decide(self,draft,operation_id=None,**changes):
        return self.witness.decide(draft,operation_id=operation_id or self.op1,
                                   epoch=changes.get("epoch","e1"))

    def test_lost_ack_lookup_does_not_second_cas(self):
        draft=self.proposal()
        received=self.decide(draft)
        self.assertEqual(self.witness.lookup(draft,operation_id=self.op1,epoch="e1"),
                         received)
        self.assertEqual(self.decide(draft),received)
        self.assertEqual(self.witness.observe(epoch="e1"),draft.next_anchor)
        self.assertEqual(self.witness.lost_reply(self.j0,draft,
                         operation_id=self.op1,epoch="e1").code,
                         "DECIDED_NOT_FINALIZED")

    def test_already_finalized_lab_is_not_clinical_ack(self):
        draft=self.proposal()
        self.decide(draft)
        self.assertEqual(self.witness.lost_reply(draft.candidate,draft,
                         operation_id=self.op1,epoch="e1").code,
                         "DECIDED_LOCAL_REVIEW_REQUIRED")

    def test_lost_reply_before_decision_uses_only_same_operation(self):
        draft=self.proposal()
        self.assertEqual(self.witness.lost_reply(self.j0,draft,
                         operation_id=self.op1,epoch="e1").code,
                         "UNKNOWN_RETRY_SAME_OP_ONLY")
        self.assertEqual(self.witness.observe(epoch="e1"),self.a0)

    def test_same_op_different_encrypted_candidate_refused(self):
        first=self.proposal()
        other=self.proposal(kid="cd"*16)
        self.decide(first)
        with self.assertRaisesRegex(w.WitnessLabError,"IDEMPOTENCY_CONFLICT"):
            self.decide(other)
        with self.assertRaisesRegex(w.WitnessLabError,"IDEMPOTENCY_CONFLICT"):
            self.witness.lookup(other,operation_id=self.op1,epoch="e1")

    def test_second_operation_stale_fork_refused(self):
        a=self.proposal()
        b=self.proposal(kid="cd"*16)
        self.decide(a)
        with self.assertRaisesRegex(w.WitnessLabError,"STALE_FORK"):
            self.decide(b,operation_id=self.op2)
        self.assertEqual(self.witness.lost_reply(self.j0,b,
                         operation_id=self.op2,epoch="e1").code,
                         "UNDECIDED_STALE_HEAD_REFUSE")

    def test_archive_missing_does_not_resolve_authority_ahead(self):
        first=self.proposal()
        self.decide(first)
        self.assertEqual(self.witness.assess_archive(self.j0,None,epoch="e1").code,
                         "INDEPENDENT_ARCHIVE_REQUIRED")

    def test_complete_authenticated_archive_needs_human_gate(self):
        first=self.proposal()
        self.decide(first)
        result=self.witness.assess_archive(self.j0,first.candidate,epoch="e1")
        self.assertEqual(result.code,"COMPLETE_EVIDENCE_HUMAN_GATE_REQUIRED")
        self.assertEqual(self.witness.observe(epoch="e1"),first.next_anchor)

    def test_archived_fork_refused_even_if_valid_other_candidate(self):
        first=self.proposal()
        other=self.proposal(kid="cd"*16)
        self.decide(first)
        self.assertEqual(self.witness.assess_archive(self.j0,other.candidate,
                         epoch="e1").code,"ARCHIVE_UNTRUSTED_REFUSE")

    def test_corrupt_local_prefix_refused(self):
        first=self.proposal()
        self.decide(first)
        corrupted_record=replace(self.j0.records[0],mac="0"*64)
        local=j.Journal((corrupted_record,))
        self.assertEqual(self.witness.assess_archive(local,first.candidate,
                         epoch="e1").code,"LOCAL_PREFIX_FORK_REFUSE")

    def test_authentic_archive_but_missing_journal_key_refused(self):
        first=self.proposal()
        self.decide(first)
        # Corrupt archive event (even if signature-looking MAC remains).
        rec=first.candidate.records[-1]
        bad=replace(rec.snapshot,candidate=rec.snapshot.candidate[:-1]+
                    bytes([rec.snapshot.candidate[-1] ^ 1]))
        archive=j.Journal(first.candidate.records[:-1]+(replace(rec,snapshot=bad),))
        self.assertEqual(self.witness.assess_archive(self.j0,archive,
                         epoch="e1").code,"ARCHIVE_UNTRUSTED_REFUSE")

    def test_missing_decision_ledger_blocks_even_valid_archive(self):
        first=self.proposal()
        self.decide(first)
        self.witness._decisions.clear()  # adversarial in-memory state loss
        self.assertEqual(self.witness.assess_archive(self.j0,first.candidate,
                         epoch="e1").code,"DECISION_LEDGER_INCOMPLETE_REFUSE")

    def test_multiple_suffix_events_require_complete_ledger(self):
        first=self.proposal()
        self.decide(first)
        state=m.verify(first.candidate.records[-1].snapshot,
                       expected_revision=1,legacy_key=self.legacy_key,
                       keys=self.keys)
        second=self.proposal(base=first.candidate,anchor=first.next_anchor,
                             state=state)
        self.decide(second,operation_id=self.op2)
        self.assertEqual(self.witness.assess_archive(self.j0,second.candidate,
                         epoch="e1").code,"COMPLETE_EVIDENCE_HUMAN_GATE_REQUIRED")
        self.witness._decisions.pop(self.op1)
        self.assertEqual(self.witness.assess_archive(self.j0,second.candidate,
                         epoch="e1").code,"DECISION_LEDGER_INCOMPLETE_REFUSE")

    def test_old_receipt_does_not_establish_current_highwatermark(self):
        first=self.proposal()
        first_receipt=self.decide(first)
        state=m.verify(first.candidate.records[-1].snapshot,
                       expected_revision=1,legacy_key=self.legacy_key,
                       keys=self.keys)
        second=self.proposal(base=first.candidate,anchor=first.next_anchor,
                             state=state)
        self.decide(second,operation_id=self.op2)
        self.assertEqual(self.witness.lookup(first,operation_id=self.op1,epoch="e1"),
                         first_receipt)
        self.assertEqual(self.witness.lost_reply(self.j0,first,
                         operation_id=self.op1,epoch="e1").code,
                         "OLD_DECISION_RECHECK_CURRENT_HEAD")

    def test_epoch_and_operation_shapes_refused(self):
        draft=self.proposal()
        with self.assertRaisesRegex(w.WitnessLabError,"EPOCH_REFUSED"):
            self.decide(draft,epoch="e0")
        for bad in ("a",0,True,None,"0"*32,"F"*32):
            with self.subTest(op=bad):
                with self.assertRaisesRegex(w.WitnessLabError,"OPERATION_ID_INVALID"):
                    self.witness.decide(draft,operation_id=bad,epoch="e1")
        self.assertEqual(self.witness.observe(epoch="e1"),self.a0)
        with self.assertRaisesRegex(w.WitnessLabError,"PROPOSAL_INVALID"):
            self.witness.decide(None,operation_id=self.op1,epoch="e1")

    def test_equal_current_head_is_not_recovery_proof_of_rollback(self):
        first=self.proposal()
        self.decide(first)
        reset=w.VolatileDecisionWitness(
            self.j0,self.a0,epoch="e1",opaque_scope="a"*32,
            journal_key=self.journal_key,legacy_key=self.legacy_key,keys=self.keys
        )
        self.assertEqual(reset.assess_archive(self.j0,None,epoch="e1").code,
                         "ALIGNED_NO_CLINICAL_ACK")
        self.assertNotEqual(reset.observe(epoch="e1"),
                            self.witness.observe(epoch="e1"))

    def test_local_ahead_missing_or_divergent_refuses(self):
        first=self.proposal()
        self.assertEqual(self.witness.assess_archive(first.candidate,None,
                         epoch="e1").code,"LOCAL_AHEAD_REFUSE")
        self.assertEqual(self.witness.assess_archive(None,first.candidate,
                         epoch="e1").code,"LOCAL_EVIDENCE_MISSING")
        self.decide(first)
        other=self.proposal(kid="cd"*16)
        self.assertEqual(self.witness.assess_archive(other.candidate,None,
                         epoch="e1").code,"LOCAL_DIVERGENCE_REFUSE")

    def test_no_live_wiring_or_io(self):
        root=Path(__file__).resolve().parents[1]
        source=(root/"witness_recovery_lab.py").read_text(encoding="utf-8")
        for forbidden in ("sqlite3","os.replace","os.fsync","Path(","open(",
                          "HotFolder(","requests","subprocess"):
            self.assertNotIn(forbidden,source)
        for active in ("gateway.py","cli.py"):
            self.assertNotIn("witness_recovery_lab",
                             (root/active).read_text(encoding="utf-8"))
        with self.assertRaises(FrozenInstanceError):
            w.Assessment("REFUSE").code="ALLOWED"


if __name__=="__main__":
    unittest.main()
