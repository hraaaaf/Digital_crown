"""LOT06-L simulated fork collision, stale head, crash and replay tests."""
from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import unittest

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway import fork_lab as f
from tools.imaging_gateway import journal_lab as j
from tools.imaging_gateway import migration_lab as m


class ForkArbitrationTests(unittest.TestCase):
    def setUp(self):
        self.clear=b"\x89PNG\r\n\x1a\nsynthetic-06-l-only"
        self.digest=hashlib.sha256(self.clear).hexdigest()
        self.legacy_key=b"L"*32
        self.journal_key=b"J"*32
        self.kid1="ab"*16
        self.kid2="cd"*16
        self.keys={self.kid1:b"T"*32,self.kid2:b"U"*32}
        identity="e"*64
        aad=("DC06A|clinic_lab|station_lab|"+identity).encode("ascii")
        nonce=b"synthetic123"
        self.legacy=b"DC6A"+nonce+AESGCM(self.legacy_key).encrypt(
            nonce,self.clear,aad
        )
        self.s0=m.begin(self.legacy,cabinet="clinic_lab",
                        workstation="station_lab",identity=identity,
                        digest=self.digest,legacy_key=self.legacy_key)
        self.base,self.anchor=j.initialize(
            self.s0,journal_key=self.journal_key,
            legacy_key=self.legacy_key,keys=self.keys
        )
        self.authority=f.VolatileAuthority(
            self.base,self.anchor,journal_key=self.journal_key,
            legacy_key=self.legacy_key,keys=self.keys
        )

    def prepared(self,kid=None):
        return m.prepare(
            self.s0,expected_revision=0,legacy_key=self.legacy_key,
            target_key_id=self.kid1 if kid is None else kid,
            keys=self.keys
        )

    def proposal(self,state=None,base=None,expected=None):
        return f.propose(
            self.base if base is None else base,
            self.anchor if expected is None else expected,
            self.prepared() if state is None else state,
            journal_key=self.journal_key,legacy_key=self.legacy_key,
            keys=self.keys
        )

    def test_first_writer_wins_and_second_fork_fails(self):
        left=self.proposal(state=self.prepared(self.kid1))
        right=self.proposal(state=self.prepared(self.kid2))
        self.assertNotEqual(left.next_anchor.mac,right.next_anchor.mac)
        self.assertEqual(self.authority.recover(self.base).phase,"SOURCE")
        self.assertEqual(self.authority.compare_and_swap(left),left.next_anchor)
        with self.assertRaisesRegex(f.ForkLabError,"STALE_FORK"):
            self.authority.compare_and_swap(right)
        with self.assertRaisesRegex(f.ForkLabError,"RECOVERY_REFUSED"):
            self.authority.recover(right.candidate)
        self.assertEqual(self.authority.recover(left.candidate).phase,"PREPARED")

    def test_reverse_winner_order_and_resubmission_refused(self):
        left=self.proposal(state=self.prepared(self.kid1))
        right=self.proposal(state=self.prepared(self.kid2))
        self.authority.compare_and_swap(right)
        for stale in (left,right):
            with self.assertRaisesRegex(f.ForkLabError,"STALE_FORK"):
                self.authority.compare_and_swap(stale)
        self.assertEqual(self.authority.observe(),right.next_anchor)

    def test_fail_closed_across_crash_boundaries(self):
        draft=self.proposal()
        # No new journal/authority publication has occurred.
        self.assertEqual(self.authority.recover(self.base).phase,"SOURCE")
        # Local journal write 'happened', authority remains old.
        with self.assertRaisesRegex(f.ForkLabError,"RECOVERY_REFUSED"):
            self.authority.recover(draft.candidate)
        self.assertEqual(self.authority.recover(self.base).phase,"SOURCE")
        # Authority advanced, but new local journal 'lost'.
        self.authority.compare_and_swap(draft)
        with self.assertRaisesRegex(f.ForkLabError,"RECOVERY_REFUSED"):
            self.authority.recover(self.base)
        self.assertEqual(self.authority.recover(draft.candidate).phase,"PREPARED")

    def test_replayed_old_head_and_forked_candidate_cannot_recover(self):
        a=self.proposal(state=self.prepared(self.kid1))
        b=self.proposal(state=self.prepared(self.kid2))
        self.authority.compare_and_swap(a)
        for local in (self.base,j.Journal(a.candidate.records[:-1]),
                      j.Journal(a.candidate.records[::-1]),b.candidate):
            with self.assertRaisesRegex(f.ForkLabError,"RECOVERY_REFUSED"):
                self.authority.recover(local)
        self.assertEqual(self.authority.recover(a.candidate).phase,"PREPARED")

    def test_stale_initial_journal_cannot_append_new_verified_state(self):
        draft=self.proposal()
        self.authority.compare_and_swap(draft)
        verified=m.verify(draft.candidate.records[-1].snapshot,
                          expected_revision=1,legacy_key=self.legacy_key,
                          keys=self.keys)
        with self.assertRaisesRegex(f.ForkLabError,"DRAFT_REJECTED"):
            self.proposal(state=verified,base=self.base,expected=self.anchor)
        good=self.proposal(state=verified,base=draft.candidate,
                           expected=draft.next_anchor)
        self.assertEqual(self.authority.compare_and_swap(good),good.next_anchor)
        self.assertEqual(self.authority.recover(good.candidate).phase,"VERIFIED")

    def test_invalid_drafts_never_advance_anchor(self):
        good=self.proposal()
        for bad in (None,good.candidate,"wrong"):
            with self.assertRaisesRegex(f.ForkLabError,"DRAFT_INVALID"):
                self.authority.compare_and_swap(bad)
        for bad in (
            replace(good,next_anchor=replace(good.next_anchor,sequence=3)),
            replace(good,candidate=j.Journal(good.candidate.records[::-1])),
            replace(good,candidate=j.Journal(
                (replace(good.candidate.records[0],mac="0"*64),
                 good.candidate.records[1])
            )),
            replace(good,next_anchor=replace(good.next_anchor,mac="0"*64)),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(f.ForkLabError):
                    self.authority.compare_and_swap(bad)
                self.assertEqual(self.authority.observe(),self.anchor)

    def test_wrong_expected_anchor_cannot_be_used_to_advance(self):
        draft=self.proposal()
        for anchor in (None,j.TrustedAnchor(True,self.anchor.mac),
                       j.TrustedAnchor(1,"fake"),j.TrustedAnchor(1,123)):
            with self.subTest(anchor=anchor):
                with self.assertRaisesRegex(f.ForkLabError,"STALE_FORK"):
                    self.authority.compare_and_swap(replace(draft,expected=anchor))
        self.assertEqual(self.authority.observe(),self.anchor)

    def test_scope_and_authentication_tamper_refused(self):
        good=self.proposal()
        s=good.candidate.records[-1].snapshot
        for altered in (
            replace(s,workstation="other_station"),
            replace(s,identity="f"*64),
            replace(s,candidate=s.candidate[:-1]+bytes([s.candidate[-1] ^ 1])),
        ):
            forged=replace(
                good,candidate=j.Journal(good.candidate.records[:-1]+(
                    replace(good.candidate.records[-1],snapshot=altered),
                ))
            )
            with self.assertRaisesRegex(f.ForkLabError,"DRAFT_INVALID"):
                self.authority.compare_and_swap(forged)
        self.assertEqual(self.authority.observe(),self.anchor)

    def test_wrong_journal_key_for_new_proposal_rejected(self):
        with self.assertRaisesRegex(f.ForkLabError,"DRAFT_REJECTED"):
            f.propose(self.base,self.anchor,self.prepared(),
                      journal_key=b"X"*32,legacy_key=self.legacy_key,
                      keys=self.keys)

    def test_rollback_is_forward_append_not_authority_rewind(self):
        draft=self.proposal()
        self.authority.compare_and_swap(draft)
        back=m.rollback(draft.candidate.records[-1].snapshot,
                        expected_revision=1,legacy_key=self.legacy_key,
                        operator_confirmed=True)
        step=self.proposal(state=back,base=draft.candidate,
                           expected=draft.next_anchor)
        self.authority.compare_and_swap(step)
        self.assertEqual(self.authority.recover(step.candidate).phase,"ROLLED_BACK")
        with self.assertRaisesRegex(f.ForkLabError,"RECOVERY_REFUSED"):
            self.authority.recover(draft.candidate)

    def test_draft_immutable_and_prepare_is_read_only(self):
        draft=self.proposal()
        with self.assertRaises(FrozenInstanceError):
            draft.expected=self.anchor
        self.assertEqual(self.authority.observe(),self.anchor)

    def test_authority_reinitialization_from_stale_genesis_defeats_monotonicity(self):
        # Explicit NEGATIVE proof: the model is not actually persistent.
        draft=self.proposal()
        self.authority.compare_and_swap(draft)
        reset=f.VolatileAuthority(
            self.base,self.anchor,journal_key=self.journal_key,
            legacy_key=self.legacy_key,keys=self.keys
        )
        self.assertEqual(reset.recover(self.base).phase,"SOURCE")
        self.assertEqual(self.authority.observe(),draft.next_anchor)

    def test_genesis_and_key_boundaries(self):
        with self.assertRaisesRegex(f.ForkLabError,"GENESIS_REQUIRED"):
            f.VolatileAuthority(self.base,replace(self.anchor,sequence=2),
                                journal_key=self.journal_key,
                                legacy_key=self.legacy_key,keys=self.keys)
        with self.assertRaisesRegex(f.ForkLabError,"GENESIS_INVALID"):
            f.VolatileAuthority(self.base,self.anchor,
                                journal_key=b"X"*32,
                                legacy_key=self.legacy_key,keys=self.keys)

    def test_no_live_wiring_disk_or_sql(self):
        root=Path(__file__).resolve().parents[1]
        code=(root/"fork_lab.py").read_text(encoding="utf-8")
        for forbidden in ("sqlite3","os.replace","os.fsync","Path(","open(",
                          "HotFolder(","requests","subprocess"):
            self.assertNotIn(forbidden,code)
        for active in ("gateway.py","cli.py"):
            self.assertNotIn("fork_lab",(root/active).read_text(encoding="utf-8"))


if __name__=="__main__":
    unittest.main()
