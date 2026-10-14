"""LOT06-K adversarial journal, replay and recovery simulation (no I/O)."""
from dataclasses import replace
import hashlib
from pathlib import Path
import unittest

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tools.imaging_gateway import journal_lab as j
from tools.imaging_gateway import migration_lab as m


class AuthenticatedMigrationJournalTests(unittest.TestCase):
    def setUp(self):
        self.clear = b"\x89PNG\r\n\x1a\nsynthetic-lot06-k"
        self.digest = hashlib.sha256(self.clear).hexdigest()
        self.legacy_key = b"L" * 32
        self.target_key = b"T" * 32
        self.journal_key = b"J" * 32
        self.kid = "ab" * 16
        self.keys = {self.kid: self.target_key}
        self.scope = dict(cabinet="cabinet-lab", workstation="station1",
                          identity="c" * 64, digest=self.digest)
        nonce = b"synthetic123"
        aad = ("DC06A|cabinet-lab|station1|" + "c" * 64).encode("ascii")
        self.old = b"DC6A" + nonce + AESGCM(self.legacy_key).encrypt(
            nonce, self.clear, aad
        )
        self.s0 = m.begin(self.old, legacy_key=self.legacy_key, **self.scope)
        self.j0, self.a0 = j.initialize(
            self.s0, journal_key=self.journal_key,
            legacy_key=self.legacy_key, keys=self.keys
        )

    def check(self, ledger, anchor, **changes):
        args=dict(journal_key=self.journal_key, legacy_key=self.legacy_key, keys=self.keys)
        args.update(changes)
        return j.verify_chain(ledger, anchor, **args)

    def append(self, ledger, anchor, state):
        return j.append(ledger, anchor, state, journal_key=self.journal_key,
                        legacy_key=self.legacy_key, keys=self.keys)

    def prepared(self, previous=None):
        previous = self.s0 if previous is None else previous
        return m.prepare(previous, expected_revision=previous.revision,
                         legacy_key=self.legacy_key,
                         target_key_id=self.kid, keys=self.keys)

    def verified(self, previous):
        return m.verify(previous, expected_revision=previous.revision,
                        legacy_key=self.legacy_key, keys=self.keys)

    def committed(self, previous):
        return m.commit(previous, expected_revision=previous.revision,
                        legacy_key=self.legacy_key, keys=self.keys)

    def full_chain(self):
        p=self.prepared()
        led1, anch1=self.append(self.j0,self.a0,p)
        v=self.verified(p)
        led2, anch2=self.append(led1,anch1,v)
        c=self.committed(v)
        led3, anch3=self.append(led2,anch2,c)
        return (led1,anch1),(led2,anch2),(led3,anch3)

    def test_genesis_mac_and_full_verified_commit_chain(self):
        self.assertEqual(self.check(self.j0, self.a0), self.s0)
        (l1,a1),(l2,a2),(l3,a3)=self.full_chain()
        self.assertEqual([a.sequence for a in (self.a0,a1,a2,a3)], [1,2,3,4])
        self.assertEqual(self.check(l1,a1).phase,"PREPARED")
        self.assertEqual(self.check(l2,a2).phase,"VERIFIED")
        self.assertEqual(self.check(l3,a3).phase,"COMMITTED")
        self.assertEqual(m.read_active(self.check(l3,a3), legacy_key=self.legacy_key,
                                       keys=self.keys), self.clear)
        self.assertEqual([x.snapshot.source for x in l3.records], [self.old]*4)

    def test_fail_closed_if_suffix_deleted_against_trusted_latest_anchor(self):
        (l1,a1),(l2,a2),(l3,a3)=self.full_chain()
        for forged in (self.j0,l1,l2,
                       j.Journal(l3.records[:-1])):
            with self.subTest(len=len(forged.records)):
                with self.assertRaisesRegex(j.JournalLabError,"ANCHOR_DIVERGENCE"):
                    self.check(forged,a3)

    def test_stale_anchor_and_stale_fork_detected_against_current_anchor(self):
        (l1,a1),(l2,a2),(l3,a3)=self.full_chain()
        for stale_anchor in (self.a0,a1,a2):
            with self.assertRaisesRegex(j.JournalLabError,"ANCHOR_DIVERGENCE"):
                self.check(l3,stale_anchor)
        # An old journal+old anchor WOULD validate; real monotonic external
        # anchor must be the current a3 to protect against full rollback.
        self.assertEqual(self.check(l1,a1).phase,"PREPARED")
        with self.assertRaisesRegex(j.JournalLabError,"ANCHOR_DIVERGENCE"):
            self.append(l1,a3,self.verified(l1.records[-1].snapshot))

    def test_head_bitflip_refuses_read_and_append(self):
        (l1,a1),_,_=self.full_chain()
        corrupted=replace(l1.records[-1], mac="0"*64)
        forged=j.Journal(l1.records[:-1]+(corrupted,))
        with self.assertRaises(j.JournalLabError):
            self.check(forged,a1)
        with self.assertRaises(j.JournalLabError):
            self.append(forged,a1,self.verified(l1.records[-1].snapshot))

    def test_mid_chain_reordering_deletion_and_link_forgery(self):
        _,_,(l3,a3)=self.full_chain()
        second,third=l3.records[1],l3.records[2]
        for fake in (
            j.Journal((l3.records[0],third,second,l3.records[3])),
            j.Journal((l3.records[0],third,l3.records[3])),
            j.Journal((l3.records[0],replace(second,previous_mac="1"*64),
                       third,l3.records[3])),
        ):
            with self.assertRaises(j.JournalLabError):
                self.check(fake,a3)

    def test_authenticated_phase_forgery_and_wrong_transitions(self):
        p=self.prepared()
        l1,a1=self.append(self.j0,self.a0,p)
        with self.assertRaisesRegex(j.JournalLabError,"MIGRATION_HISTORY_INVALID"):
            self.append(l1,a1,replace(p,phase="COMMITTED",revision=2))
        with self.assertRaisesRegex(j.JournalLabError,"MIGRATION_HISTORY_INVALID"):
            self.append(self.j0,self.a0,replace(p,phase="VERIFIED"))
        with self.assertRaisesRegex(j.JournalLabError,"MIGRATION_HISTORY_INVALID"):
            self.append(l1,a1,replace(p,revision=9))
        with self.assertRaisesRegex(j.JournalLabError,"MIGRATION_HISTORY_INVALID"):
            self.append(l1,a1,replace(self.verified(p),source=b"changed"))

    def test_key_separation_wrong_mac_key_and_missing_target_key(self):
        with self.assertRaisesRegex(j.JournalLabError,"JOURNAL_KEY_REUSED"):
            j.initialize(self.s0,journal_key=self.legacy_key,
                         legacy_key=self.legacy_key,keys=self.keys)
        with self.assertRaisesRegex(j.JournalLabError,"JOURNAL_KEY_REUSED"):
            j.initialize(self.s0,journal_key=self.target_key,
                         legacy_key=self.legacy_key,keys=self.keys)
        with self.assertRaisesRegex(j.JournalLabError,"RECORD_AUTHENTICATION_FAILED"):
            self.check(self.j0,self.a0,journal_key=b"W"*32)
        (l1,a1),_,_=self.full_chain()
        with self.assertRaisesRegex(j.JournalLabError,"CHECKPOINT_UNAVAILABLE"):
            self.check(l1,a1,keys={})

    def test_wrong_legacy_key_and_corrupted_snapshot_cannot_verify(self):
        with self.assertRaisesRegex(j.JournalLabError,"CHECKPOINT_UNAVAILABLE"):
            self.check(self.j0,self.a0,legacy_key=b"Z"*32)
        bad=replace(self.j0.records[0].snapshot,source=self.old[:-1]+b"X")
        forged=j.Journal((replace(self.j0.records[0],snapshot=bad),))
        with self.assertRaisesRegex(j.JournalLabError,"CHECKPOINT_UNAVAILABLE"):
            self.check(forged,self.a0)

    def test_wrong_capture_or_scope_and_candidate_tag_corruption(self):
        (l1,a1),_,_=self.full_chain()
        checkpoint=l1.records[-1].snapshot
        for state in (
            replace(checkpoint,identity="f"*64),
            replace(checkpoint,workstation="other"),
            replace(checkpoint,candidate=checkpoint.candidate[:-1]+b"X"),
        ):
            forged=j.Journal(l1.records[:-1]+(replace(l1.records[-1],snapshot=state),))
            with self.assertRaises(j.JournalLabError):
                self.check(forged,a1)

    def test_crash_before_and_after_append_vs_external_anchor(self):
        p=self.prepared()
        # Crash before record publication: trusted anchor remains at genesis.
        self.assertEqual(self.check(self.j0,self.a0).phase,"SOURCE")
        prepared_journal,next_anchor=self.append(self.j0,self.a0,p)
        # Journal append published, anchor not yet advanced: availability fails
        # closed until external reconciliation; no invented atomicity guarantee.
        with self.assertRaisesRegex(j.JournalLabError,"ANCHOR_DIVERGENCE"):
            self.check(prepared_journal,self.a0)
        # Both advanced atomically only in memory at this point.
        self.assertEqual(self.check(prepared_journal,next_anchor).phase,"PREPARED")

    def test_explicit_rollback_is_new_authenticated_event_not_truncation(self):
        _,_,(ledger,anchor)=self.full_chain()
        old=ledger.records[-1].snapshot
        back=m.rollback(old,expected_revision=old.revision,
                        legacy_key=self.legacy_key,operator_confirmed=True)
        new,anch=self.append(ledger,anchor,back)
        self.assertEqual(self.check(new,anch).phase,"ROLLED_BACK")
        self.assertEqual(anch.sequence,anchor.sequence+1)
        self.assertEqual(new.records[-1].snapshot.source,self.old)
        with self.assertRaisesRegex(j.JournalLabError,"ANCHOR_DIVERGENCE"):
            self.check(ledger,anch)

    def test_can_explicitly_retry_after_rollback(self):
        (led,anchor),_,_=self.full_chain()
        p=led.records[-1].snapshot
        back=m.rollback(p,expected_revision=p.revision,
                        legacy_key=self.legacy_key,operator_confirmed=True)
        led,anchor=self.append(led,anchor,back)
        retry=self.prepared(back)
        led,anchor=self.append(led,anchor,retry)
        self.assertEqual(self.check(led,anchor).revision,3)
        self.assertEqual(self.check(led,anchor).phase,"PREPARED")

    def test_invalid_shapes_and_excessive_journal_rejected(self):
        for anchor in (None, j.TrustedAnchor(True,"0"*64),
                       j.TrustedAnchor(0,"0"*64),
                       j.TrustedAnchor(1,"bad")):
            with self.assertRaisesRegex(j.JournalLabError,"ANCHOR_INVALID"):
                self.check(self.j0,anchor)
        for ledger in (j.Journal(()), j.Journal([]), None,
                       j.Journal(self.j0.records*257)):
            with self.assertRaisesRegex(j.JournalLabError,"JOURNAL_INVALID"):
                self.check(ledger,self.a0)
        malformed=replace(self.j0.records[0],sequence=True)
        with self.assertRaisesRegex(j.JournalLabError,"RECORD_INVALID"):
            self.check(j.Journal((malformed,)),self.a0)
        malformed_phase=replace(self.s0,phase=["SOURCE"])
        with self.assertRaises(j.JournalLabError):
            self.check(j.Journal((replace(self.j0.records[0],snapshot=malformed_phase),)),
                       self.a0)

    def test_snapshot_types_and_scope_are_not_silently_coerced(self):
        for bad in (replace(self.s0,cabinet=42),
                    replace(self.s0,revision=True),
                    replace(self.s0,candidate=bytearray(b"x"))):
            with self.assertRaises(j.JournalLabError):
                j.initialize(bad,journal_key=self.journal_key,
                             legacy_key=self.legacy_key,keys=self.keys)

    def test_no_live_collector_service_or_persistence_wiring(self):
        root=Path(__file__).resolve().parents[1]
        source=(root/"journal_lab.py").read_text(encoding="utf-8")
        for forbidden in ("sqlite3","os.replace","os.fsync","Path(","open(",
                          "HotFolder(","subprocess","requests"):
            self.assertNotIn(forbidden,source)
        for active in ("cli.py","gateway.py"):
            self.assertNotIn("journal_lab",(root/active).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
