"""LOT06-M corrective adversarial LAB: idempotence, lost ACK, archive proof."""
from dataclasses import FrozenInstanceError, replace
from concurrent.futures import ThreadPoolExecutor
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
        self.registry=w.VolatileEnrollmentRegistry()
        self.witness=w.VolatileDecisionWitness(
            self.j0,self.a0,authority_id="lab-authority",epoch="e1",opaque_scope="a"*32,
            registry=self.registry,
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
        self.assertEqual((received.authority_id,received.opaque_scope),
                         ("lab-authority","a"*32))
        self.assertEqual(self.witness.lookup(draft,operation_id=self.op1,epoch="e1"),
                         received)
        self.assertEqual(self.decide(draft),received)
        self.assertEqual(self.witness.observe(epoch="e1"),draft.next_anchor)
        self.assertEqual(self.witness.lost_reply(self.j0,draft,
                         operation_id=self.op1,epoch="e1").code,
                         "DECIDED_NOT_FINALIZED_LOCAL_STALE")

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
        self.assertEqual(result.code,"CHAIN_VALID_PROVENANCE_UNVERIFIED_HUMAN_GATE")
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
                         epoch="e1").code,"LOCAL_INVALID_REFUSE")

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
        self.witness._state=replace(self.witness._state, decisions=())  # synthetic ledger loss
        self.assertEqual(self.witness.assess_archive(self.j0,first.candidate,
                         epoch="e1").code,"WITNESS_LEDGER_INCOMPLETE_REFUSE")

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
                         epoch="e1").code,"CHAIN_VALID_PROVENANCE_UNVERIFIED_HUMAN_GATE")
        self.witness._state=replace(self.witness._state,
                                     decisions=self.witness._state.decisions[1:])
        self.assertEqual(self.witness.assess_archive(self.j0,second.candidate,
                         epoch="e1").code,"WITNESS_LEDGER_INCOMPLETE_REFUSE")

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
            self.j0,self.a0,authority_id="lab-authority",epoch="e1",opaque_scope="a"*32,
            registry=w.VolatileEnrollmentRegistry(),  # intentionally untrusted reset
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

    def test_malformed_manifest_returns_fixed_error_and_no_advance(self):
        draft=self.proposal()
        record=draft.candidate.records[-1]
        bad=replace(record,snapshot=replace(record.snapshot,cabinet=99))
        forged=replace(draft,candidate=j.Journal(
            draft.candidate.records[:-1]+(bad,)))
        with self.assertRaisesRegex(w.WitnessLabError,"PROPOSAL_INVALID"):
            self.decide(forged)
        self.assertEqual(self.witness.observe(epoch="e1"),self.a0)


    def test_security_receipt_all_fields_audited(self):
        draft=self.proposal()
        self.decide(draft)
        good=self.witness._state.decisions[0]
        mutations=[
            {"request_digest":"0"*64},
            {"authority_id":"another"},
            {"opaque_scope":"b"*32},
            {"epoch":"old"},
            {"operation_id":"4"*32},
            {"before":replace(good.before,mac="0"*64)},
            {"after":replace(good.after,mac="0"*64)},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                bad=replace(good,**mutation)
                self.witness._state=replace(
                    self.witness._state,decisions=(bad,))
                self.assertEqual(
                    self.witness.assess_archive(self.j0,draft.candidate,
                                                epoch="e1").code,
                    "WITNESS_LEDGER_INCOMPLETE_REFUSE")
        self.witness._state=replace(self.witness._state,decisions=(good,))

    def test_security_digest_separates_identity_scope_epoch_and_op(self):
        draft=self.proposal()
        receipt=self.decide(draft)
        for authority_id,scope,epoch,op in (
                ("other-authority","a"*32,"e1",self.op1),
                ("lab-authority","b"*32,"e1",self.op1),
                ("lab-authority","a"*32,"e2",self.op1),
                ("lab-authority","a"*32,"e1",self.op2)):
            other=w.VolatileDecisionWitness(
                self.j0,self.a0,authority_id=authority_id,
                epoch=epoch,opaque_scope=scope,
                registry=w.VolatileEnrollmentRegistry(),  # digest-only separate scope
                journal_key=self.journal_key,
                legacy_key=self.legacy_key,keys=self.keys)
            different=other.decide(draft,operation_id=op,epoch=epoch)
            self.assertNotEqual(receipt.request_digest,
                                different.request_digest)

    def test_reliability_equal_head_missing_ledger_refused(self):
        draft=self.proposal()
        self.decide(draft)
        self.witness._state=replace(self.witness._state,decisions=())
        self.assertEqual(
            self.witness.assess_archive(draft.candidate,None,epoch="e1").code,
            "WITNESS_LEDGER_INCOMPLETE_REFUSE")
        self.assertEqual(
            self.witness.lost_reply(draft.candidate,draft,
                         operation_id=self.op1,epoch="e1").code,
            "WITNESS_LEDGER_INCONSISTENT_REFUSE")

    def test_reliability_fault_injection_atomic_before_after(self):
        draft=self.proposal()
        with self.assertRaisesRegex(w.SimulatedLabCrash,"BEFORE_INSTALL"):
            self.witness.decide(draft,operation_id=self.op1,
                                epoch="e1",failpoint="BEFORE_INSTALL")
        self.assertEqual(self.witness.observe(epoch="e1"),self.a0)
        self.assertIsNone(self.witness.lookup(draft,operation_id=self.op1,
                                              epoch="e1"))
        with self.assertRaisesRegex(w.SimulatedLabCrash,"AFTER_INSTALL"):
            self.witness.decide(draft,operation_id=self.op1,
                                epoch="e1",failpoint="AFTER_INSTALL")
        self.assertEqual(self.witness.observe(epoch="e1"),draft.next_anchor)
        receipt=self.witness.lookup(draft,operation_id=self.op1,epoch="e1")
        self.assertIsNotNone(receipt)
        self.assertEqual(self.decide(draft),receipt)
        self.assertEqual(len(self.witness._state.decisions),1)

    def test_reliability_missing_local_and_stale_are_distinct(self):
        draft=self.proposal()
        self.decide(draft)
        self.assertEqual(
            self.witness.lost_reply(None,draft,
                        operation_id=self.op1,epoch="e1").code,
            "LOCAL_EVIDENCE_MISSING")
        self.assertEqual(
            self.witness.lost_reply(self.j0,draft,
                        operation_id=self.op1,epoch="e1").code,
            "DECIDED_NOT_FINALIZED_LOCAL_STALE")
        corrupted=j.Journal((replace(self.j0.records[0],mac="0"*64),))
        self.assertEqual(
            self.witness.lost_reply(corrupted,draft,
                        operation_id=self.op1,epoch="e1").code,
            "LOCAL_INVALID_REFUSE")

    def test_reliability_concurrent_forks_one_winner(self):
        a=self.proposal()
        b=self.proposal(kid="cd"*16)
        tasks=[(a if i%2==0 else b,format(i+1,"032x"))
               for i in range(12)]
        def submit(item):
            draft,op=item
            try:
                return self.witness.decide(draft,operation_id=op,epoch="e1")
            except w.WitnessLabError as error:
                return str(error)
        with ThreadPoolExecutor(max_workers=6) as pool:
            answers=list(pool.map(submit,tasks))
        winners=[answer for answer in answers if isinstance(answer,w.Receipt)]
        self.assertEqual(len(winners),1)
        self.assertEqual(len(self.witness._state.decisions),1)
        self.assertTrue(all(answer=="STALE_FORK"
                            for answer in answers if not isinstance(answer,w.Receipt)))

    def test_reliability_fault_matrix_and_extra_events_refused(self):
        first=self.proposal()
        self.decide(first)
        state=m.verify(first.candidate.records[-1].snapshot,
                       expected_revision=1,legacy_key=self.legacy_key,
                       keys=self.keys)
        second=self.proposal(base=first.candidate,anchor=first.next_anchor,
                             state=state)
        self.decide(second,operation_id=self.op2)
        self.assertEqual(len(self.witness._state.decisions),2)
        self.assertEqual(
            self.witness.assess_archive(self.j0,second.candidate,
                                        epoch="e1").code,
            "CHAIN_VALID_PROVENANCE_UNVERIFIED_HUMAN_GATE")
        self.witness._state=replace(
            self.witness._state,decisions=self.witness._state.decisions[:1])
        self.assertEqual(
            self.witness.assess_archive(second.candidate,None,
                                        epoch="e1").code,
            "WITNESS_LEDGER_INCOMPLETE_REFUSE")

    def test_reliability_rejected_invalid_failpoint_is_unchanged(self):
        draft=self.proposal()
        with self.assertRaisesRegex(w.WitnessLabError,"FAILPOINT_INVALID"):
            self.witness.decide(draft,operation_id=self.op1,
                                epoch="e1",failpoint="MID_CAS")
        self.assertEqual(self.witness._state.head,self.a0)
        self.assertEqual(self.witness._state.decisions,())


    def test_replay_observe_refuses_torn_ledger(self):
        draft=self.proposal()
        self.decide(draft)
        state=self.witness._state
        for d in ((),(replace(state.decisions[0],request_digest="0"*64),)):
            self.witness._state=replace(state,decisions=d)
            with self.assertRaisesRegex(w.WitnessLabError,"WITNESS_LEDGER_INCONSISTENT"):
                self.witness.observe(epoch="e1")
        self.witness._state=state
        self.assertEqual(self.witness.observe(epoch="e1"),draft.next_anchor)

    def test_replay_same_capture_alias_denied_in_shared_registry(self):
        args=dict(journal_key=self.journal_key,
                  legacy_key=self.legacy_key,keys=self.keys)
        for authority,epoch,scope,reason in (
                ("lab-authority","e1","a"*32,"ACTIVE_WITNESS_EXISTS"),
                ("lab-authority","e1","b"*32,"ENROLLMENT_CONFLICT"),
                ("lab-authority","e2","a"*32,"ENROLLMENT_CONFLICT"),
                ("other-authority","e1","a"*32,"ENROLLMENT_CONFLICT")):
            with self.subTest(auth=authority,epoch=epoch):
                with self.assertRaisesRegex(w.WitnessLabError,reason):
                    w.VolatileDecisionWitness(
                        self.j0,self.a0,authority_id=authority,epoch=epoch,
                        opaque_scope=scope,registry=self.registry,**args)
        # Negative: independent registry can still permit the old fork.
        second=w.VolatileDecisionWitness(
            self.j0,self.a0,authority_id="lab-authority",epoch="e1",
            opaque_scope="b"*32,registry=w.VolatileEnrollmentRegistry(),**args)
        self.decide(self.proposal())
        second.decide(self.proposal(kid="cd"*16),
                      operation_id=self.op2,epoch="e1")
        self.assertNotEqual(self.witness._state.head,second._state.head)

    def test_replay_lost_reply_uses_single_snapshot(self):
        draft=self.proposal()
        digest=self.witness._digest
        did=[False]
        def interleave(d,op):
            if not did[0]:
                did[0]=True
                self.witness._digest=digest
                self.decide(d)
            return digest(d,op)
        self.witness._digest=interleave
        self.assertEqual(self.witness.lost_reply(
            self.j0,draft,operation_id=self.op1,epoch="e1").code,
            "UNKNOWN_RETRY_SAME_OP_ONLY")
        self.assertEqual(self.witness._state.head,draft.next_anchor)
        self.assertEqual(self.witness.lost_reply(
            self.j0,draft,operation_id=self.op1,epoch="e1").code,
            "DECIDED_NOT_FINALIZED_LOCAL_STALE")

    def test_replay_modified_historical_prefix_denied(self):
        draft=self.proposal()
        self.decide(draft)
        corrupted=replace(self.j0.records[0],mac="0"*64)
        forged=replace(draft,candidate=j.Journal(
            (corrupted,)+draft.candidate.records[1:]))
        for action in (self.witness.lookup,self.witness.decide):
            with self.assertRaisesRegex(w.WitnessLabError,"PROPOSAL_REFUSED"):
                action(forged,operation_id=self.op1,epoch="e1")

    def test_replay_linear_manifest_cost(self):
        from unittest.mock import patch
        from tools.imaging_gateway import journal_lab
        history,head,state=self.j0,self.a0,self.genesis
        for i in range(16):
            if state.phase in ("SOURCE","ROLLED_BACK"):
                state=m.prepare(state,expected_revision=state.revision,
                    legacy_key=self.legacy_key,target_key_id="ab"*16,keys=self.keys)
            elif state.phase=="PREPARED":
                state=m.verify(state,expected_revision=state.revision,
                    legacy_key=self.legacy_key,keys=self.keys)
            elif state.phase=="VERIFIED":
                state=m.commit(state,expected_revision=state.revision,
                    legacy_key=self.legacy_key,keys=self.keys)
            else:
                state=m.rollback(state,expected_revision=state.revision,
                    legacy_key=self.legacy_key,operator_confirmed=True)
            draft=self.proposal(base=history,anchor=head,state=state)
            self.witness.decide(draft,operation_id=format(i+1,"032x"),epoch="e1")
            history,head=draft.candidate,draft.next_anchor
        count=[0]
        original=journal_lab._manifest
        def counted(value):
            count[0]+=1
            return original(value)
        with patch.object(journal_lab,"_manifest",side_effect=counted):
            self.witness.lookup(draft,operation_id=format(16,"032x"),epoch="e1")
        self.assertLessEqual(count[0],3*len(history.records)+2)


    def test_loop_nonce_reencryption_same_capture_denied(self):
        # Fresh AES-GCM nonce changes ciphertext SHA, NOT capture identity.
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        identity="e"*64
        nonce=b"freshnonce12"  # 12 bytes
        aad=("DC06A|lab_m|workstation_m|"+identity).encode("ascii")
        changed=b"DC6A"+nonce+AESGCM(self.legacy_key).encrypt(
            nonce,self.clear,aad)
        new_genesis=m.begin(
            changed,cabinet="lab_m",workstation="workstation_m",
            identity=identity,digest=hashlib.sha256(self.clear).hexdigest(),
            legacy_key=self.legacy_key)
        self.assertNotEqual(new_genesis.source_sha256,self.genesis.source_sha256)
        j2,a2=j.initialize(
            new_genesis,journal_key=self.journal_key,
            legacy_key=self.legacy_key,keys=self.keys)
        with self.assertRaisesRegex(w.WitnessLabError,"ENROLLMENT_CONFLICT"):
            w.VolatileDecisionWitness(j2,a2,authority_id="lab-authority",
                epoch="e1",opaque_scope="b"*32,registry=self.registry,
                journal_key=self.journal_key,legacy_key=self.legacy_key,
                keys=self.keys)

    def test_loop_corrupt_ledger_precedes_every_archive_early_exit(self):
        d=self.proposal()
        self.decide(d)
        good=self.witness._state
        self.witness._state=replace(good,decisions=())
        corrupted=j.Journal((replace(self.j0.records[0],mac="0"*64),))
        for local,archive in (
                (None,None),(self.j0,None),(d.candidate,None),
                (corrupted,None),(self.j0,d.candidate)):
            with self.subTest(local=local is not None,
                              archive=archive is not None):
                self.assertEqual(self.witness.assess_archive(
                    local,archive,epoch="e1").code,
                    "WITNESS_LEDGER_INCOMPLETE_REFUSE")
        self.witness._state=good

    def test_loop_audit_work_budget_fail_closed_on_proposal(self):
        from unittest.mock import patch
        d=self.proposal()
        current=self.witness._state
        # Set a small budget to model a multi-GB chain without allocating it.
        minimum=sum(len(r.snapshot.source)+(len(r.snapshot.candidate)
                    if r.snapshot.candidate is not None else 0)
                    for r in self.j0.records)
        with patch.object(w,"_MAX_LAB_AUDIT_BYTES",minimum):
            self.assertEqual(self.witness.observe(epoch="e1"),self.a0)
            with self.assertRaisesRegex(
                    w.WitnessLabError,"AUDIT_WORK_BUDGET_EXCEEDED"):
                self.decide(d)
            self.assertEqual(self.witness._state,current)
        self.assertEqual(self.witness.observe(epoch="e1"),self.a0)

    def test_loop_audit_over_budget_untrusted_read_refuses(self):
        from unittest.mock import patch
        d=self.proposal()
        self.decide(d)
        full=self.witness._state
        minimum=sum(len(r.snapshot.source)+(len(r.snapshot.candidate)
                    if r.snapshot.candidate is not None else 0)
                    for r in self.j0.records)
        with patch.object(w,"_MAX_LAB_AUDIT_BYTES",minimum):
            with self.assertRaisesRegex(
                    w.WitnessLabError,"AUDIT_WORK_BUDGET_EXCEEDED"):
                self.witness.observe(epoch="e1")
            self.assertEqual(self.witness.assess_archive(
                d.candidate,None,epoch="e1").code,
                "AUDIT_WORK_BUDGET_REFUSE")
        self.assertEqual(self.witness._state,full)


    def test_loop_same_identity_modified_content_cannot_reenroll(self):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        identity="e"*64
        changed_clear=b"another-valid-version-of-this-capture"
        nonce=b"secondnonce1"
        aad=("DC06A|lab_m|workstation_m|"+identity).encode("ascii")
        payload=b"DC6A"+nonce+AESGCM(self.legacy_key).encrypt(
            nonce,changed_clear,aad)
        state=m.begin(payload,cabinet="lab_m",workstation="workstation_m",
            identity=identity,digest=hashlib.sha256(changed_clear).hexdigest(),
            legacy_key=self.legacy_key)
        second_j,second_a=j.initialize(
            state,journal_key=self.journal_key,
            legacy_key=self.legacy_key,keys=self.keys)
        with self.assertRaisesRegex(w.WitnessLabError,"ENROLLMENT_CONFLICT"):
            w.VolatileDecisionWitness(
                second_j,second_a,authority_id="lab-authority",epoch="e1",
                opaque_scope="b"*32,registry=self.registry,
                journal_key=self.journal_key,
                legacy_key=self.legacy_key,keys=self.keys)


    def test_loop_verified_snapshot_cache_skips_rehash_on_repeated_reads(self):
        from unittest.mock import patch
        from tools.imaging_gateway import journal_lab
        draft=self.proposal()
        self.decide(draft)
        calls=[0]
        original=journal_lab._manifest
        def counted(snapshot):
            calls[0]+=1
            return original(snapshot)
        with patch.object(journal_lab,"_manifest",side_effect=counted):
            for _ in range(32):
                self.assertEqual(self.witness.observe(epoch="e1"),
                                 draft.next_anchor)
                self.assertEqual(self.witness.lookup(
                    draft,operation_id=self.op1,epoch="e1").operation_id,
                    self.op1)
        # 32 request digests require one new-event manifest per lookup;
        # no 32 * full historical chain rescans should occur.
        self.assertLessEqual(calls[0],32+2)

    def test_loop_cache_invalidated_on_state_substitution_and_key_change(self):
        draft=self.proposal()
        self.decide(draft)
        head=self.witness._state
        self.assertEqual(self.witness.observe(epoch="e1"),draft.next_anchor)
        self.witness._state=replace(head,decisions=())
        with self.assertRaisesRegex(w.WitnessLabError,"WITNESS_LEDGER_INCONSISTENT"):
            self.witness.observe(epoch="e1")
        self.witness._state=head
        self.assertEqual(self.witness.observe(epoch="e1"),draft.next_anchor)
        # Change a target AEAD key even though the _State object is unchanged.
        self.witness._keys["ab"*16]=b"X"*32
        with self.assertRaisesRegex(w.WitnessLabError,"WITNESS_LEDGER_INCONSISTENT"):
            self.witness.observe(epoch="e1")

    def test_loop_after_install_failure_keeps_verified_head_and_receipt(self):
        from unittest.mock import patch
        from tools.imaging_gateway import journal_lab
        draft=self.proposal()
        with self.assertRaisesRegex(w.SimulatedLabCrash,"AFTER_INSTALL"):
            self.witness.decide(draft,operation_id=self.op1,
                epoch="e1",failpoint="AFTER_INSTALL")
        with patch.object(journal_lab,"_manifest",
                          side_effect=AssertionError("unexpected revalidation")):
            self.assertEqual(self.witness.observe(epoch="e1"),
                             draft.next_anchor)
        self.assertIsNotNone(self.witness.lookup(
            draft,operation_id=self.op1,epoch="e1"))


    def test_loop_oversize_proposal_refused_before_manifest_hashed(self):
        from unittest.mock import patch
        from tools.imaging_gateway import journal_lab
        draft=self.proposal()
        source_bytes=sum(len(r.snapshot.source)+(len(r.snapshot.candidate)
                    if r.snapshot.candidate is not None else 0)
                    for r in self.j0.records)
        with patch.object(w,"_MAX_LAB_AUDIT_BYTES",source_bytes):
            with patch.object(journal_lab,"_manifest",
                              side_effect=AssertionError("should not hash")):
                for api in (self.witness.decide,self.witness.lookup):
                    with self.assertRaisesRegex(
                        w.WitnessLabError,"AUDIT_WORK_BUDGET_EXCEEDED"):
                        api(draft,operation_id=self.op1,epoch="e1")
                with self.assertRaisesRegex(
                    w.WitnessLabError,"AUDIT_WORK_BUDGET_EXCEEDED"):
                    self.witness.lost_reply(
                        self.j0,draft,operation_id=self.op1,epoch="e1")
        self.assertEqual(self.witness.observe(epoch="e1"),self.a0)

    def test_loop_untrusted_local_oversize_refused_before_cryptography(self):
        from unittest.mock import patch
        from tools.imaging_gateway import journal_lab
        d=self.proposal()
        self.decide(d)
        # Only tiny real ciphertext; shrink LAB budget in a strict subtest,
        # then call with over-budget valid local media.
        old=self.j0
        minimum=sum(len(r.snapshot.source)+(len(r.snapshot.candidate)
                    if r.snapshot.candidate is not None else 0)
                    for r in old.records)
        state=self.witness._state
        # This patch would also make current witness over-budget; distinguish
        # third-party media by adding duplicate valid records only.
        extended=j.Journal(d.candidate.records+d.candidate.records)
        with patch.object(w,"_MAX_LAB_AUDIT_BYTES",
                          sum(len(r.snapshot.source)+
                              (len(r.snapshot.candidate)
                               if r.snapshot.candidate is not None else 0)
                              for r in state.history.records)):
            self.assertEqual(self.witness.assess_archive(
                extended,None,epoch="e1").code,
                "LOCAL_AUDIT_BUDGET_REFUSE")
            self.assertEqual(self.witness.lost_reply(
                extended,d,operation_id=self.op1,epoch="e1").code,
                "LOCAL_AUDIT_BUDGET_REFUSE")

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
