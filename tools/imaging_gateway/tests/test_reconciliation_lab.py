"""LOT06-M synthetic negative matrix. No real authority or persistence."""
from dataclasses import FrozenInstanceError, replace
import hashlib
from pathlib import Path
import unittest
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tools.imaging_gateway import journal_lab as j
from tools.imaging_gateway import migration_lab as m
from tools.imaging_gateway import reconciliation_lab as r


class RecoveryMatrixTests(unittest.TestCase):
    def setUp(self):
        clear = b"\\x89PNG\\r\\n\\x1a\\nlab-only-M".decode("unicode_escape").encode("latin1")
        old_key, journal_key = b"L"*32, b"J"*32
        kid = "ab"*16
        keys = {kid:b"T"*32}
        identity = "e"*64
        nonce = b"synthetic123"
        aad = ("DC06A|lab_m|workstation_m|"+identity).encode("ascii")
        old = b"DC6A"+nonce+AESGCM(old_key).encrypt(nonce,clear,aad)
        start = m.begin(old,cabinet="lab_m",workstation="workstation_m",
                        identity=identity,digest=hashlib.sha256(clear).hexdigest(),
                        legacy_key=old_key)
        self.j0,self.a0 = j.initialize(start,journal_key=journal_key,
                                      legacy_key=old_key,keys=keys)
        state = m.prepare(start,expected_revision=0,legacy_key=old_key,
                          target_key_id=kid,keys=keys)
        self.j1,self.a1 = j.append(self.j0,self.a0,state,journal_key=journal_key,
                                   legacy_key=old_key,keys=keys)
        self.params=dict(expected_epoch="e1",supplied_epoch="e1",
                         journal_key=journal_key,legacy_key=old_key,keys=keys)

    def inspect(self,local,anchor,**changes):
        kwargs=dict(self.params)
        kwargs.update(changes)
        return r.inspect(local,anchor,**kwargs)

    def test_matches_are_not_auto_commits(self):
        self.assertEqual(self.inspect(self.j1,self.a1),r.Finding("VERIFIED_MATCH","PREPARED"))

    def test_local_ahead_denied(self):
        self.assertEqual(self.inspect(self.j1,self.a0).code,"LOCAL_AHEAD")

    def test_authority_ahead_denied(self):
        self.assertEqual(self.inspect(self.j0,self.a1).code,"AUTHORITY_AHEAD")

    def test_same_sequence_conflicting_mac_denied(self):
        self.assertEqual(self.inspect(self.j1,replace(self.a1,mac="0"*64)).code,
                         "HEAD_MISMATCH")

    def test_missing_authority_and_epoch_conflict_denied(self):
        self.assertEqual(self.inspect(self.j1,None).code,"AUTHORITY_UNKNOWN")
        self.assertEqual(self.inspect(self.j1,self.a1,supplied_epoch="e0").code,
                         "EPOCH_CONFLICT")
        self.assertEqual(self.inspect(self.j1,self.a1,supplied_epoch=None).code,
                         "AUTHORITY_UNKNOWN")

    def test_invalid_shape_or_missing_keys_denied(self):
        self.assertEqual(self.inspect(j.Journal(()),self.a1).code,"LOCAL_INVALID")
        self.assertEqual(self.inspect(self.j1,self.a1,keys={}).code,
                         "INTEGRITY_OR_KEY_FAILURE")
        self.assertEqual(self.inspect(None,self.a1).code,"LOCAL_INVALID")

    def test_media_tampering_refused(self):
        rec=self.j1.records[-1]
        corrupted=replace(rec.snapshot,candidate=rec.snapshot.candidate[:-1]+
                          bytes([rec.snapshot.candidate[-1]^1]))
        invalid=j.Journal(self.j1.records[:-1]+(replace(rec,snapshot=corrupted),))
        self.assertEqual(self.inspect(invalid,self.a1).code,
                         "INTEGRITY_OR_KEY_FAILURE")

    def test_restoring_both_old_objects_fools_caller_owned_anchor_negative(self):
        self.assertEqual(self.inspect(self.j0,self.a0).code,"VERIFIED_MATCH")
        self.assertEqual(self.inspect(self.j0,self.a1).code,"AUTHORITY_AHEAD")

    def test_no_live_wiring(self):
        root=Path(__file__).resolve().parents[1]
        source=(root/"reconciliation_lab.py").read_text(encoding="utf-8")
        for forbidden in ("sqlite3","os.replace","os.fsync","Path(","open(",
                          "HotFolder(","requests","subprocess"):
            self.assertNotIn(forbidden,source)
        for active in ("gateway.py","cli.py"):
            self.assertNotIn("reconciliation_lab",
                             (root/active).read_text(encoding="utf-8"))
        with self.assertRaises(FrozenInstanceError):
            r.Finding("LOCAL_AHEAD").code="VERIFIED_MATCH"


if __name__=="__main__":
    unittest.main()
