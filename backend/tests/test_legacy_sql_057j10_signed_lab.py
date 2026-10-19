"""Actual RSA and committed SQLite WAL + media/vault FAKE copy negative tests."""
import base64
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import shutil
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
# Only the two unmodified recovery modules are under test here. The package
# backend/__init__.py eagerly initialises unrelated clinical SQLAlchemy models
# and media policies; loading that application shell is not part of an OFFLINE
# fake recovery test. Preserve actual source/module imports in a minimal namespace.
import sys
import types
if "backend" not in sys.modules:
    _backend = types.ModuleType("backend")
    _backend.__path__ = [str(Path(__file__).resolve().parents[1])]
    _backend.__package__ = "backend"
    sys.modules["backend"] = _backend

from backend.services.legacy_migration_safe_restore_lab_v15 import (
    publish_fake_snapshot, read_fake_current, FakeRecoveryDenied)
from backend.services import legacy_migration_j10_signed_offline_lab_v15 as j

class J10SignedOfflineLab(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="lot05j_fake_")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.inputs=self.root/"inputs"
        self.inputs.mkdir()
        (self.inputs/"media-fake").mkdir()
        for name,data in (("license_fake.bin",b"FAKE-LICENSE"),
                          ("media-fake/scan.fake",b"FAKE-SCAN"),
                          ("media-fake/invoice.fake",b"FAKE-INVOICE")):
            (self.inputs/name).write_bytes(data)
        self.cn=sqlite3.connect(str(self.inputs/"clinical.db"))
        self.addCleanup(self.cn.close)
        self.assertEqual(self.cn.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower(),"wal")
        self.cn.execute("PRAGMA wal_autocheckpoint=0")
        self.cn.execute("CREATE TABLE fake_truth (v TEXT)")
        self.cn.execute("INSERT INTO fake_truth VALUES ('COMMITTED_WAL')")
        self.cn.commit()
        self.assertTrue(Path(str(self.inputs/"clinical.db")+"-wal").stat().st_size>0)
        self.private=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.pin=self.private.public_key().public_bytes(serialization.Encoding.PEM,
                                                        serialization.PublicFormat.SubjectPublicKeyInfo)
        self.job=secrets.token_hex(16)
        self.output=self.root/"isolated-recovery"
        flag=patch.dict(os.environ,{j.FLAG:"1"})
        flag.start()
        self.addCleanup(flag.stop)

    def publish(self):
        publish_fake_snapshot(self.root,self.cn,request_owner=7,expected_owner=7)

    def sign(self,**updates):
        _,record=read_fake_current(self.root,request_owner=7,expected_owner=7)
        now=int(time.time())
        claims=dict(v=1,purpose=j.PURPOSE,owner=7,job=self.job,
                    generation=record["generation"],manifest=j.digest(record),
                    nonce=secrets.token_hex(16),issued=now,expires=now+90)
        claims.update(updates)
        sig=self.private.sign(j.canonical(claims),padding.PKCS1v15(),hashes.SHA256())
        return j.canonical({"claims":claims,"signature":base64.b64encode(sig).decode("ascii")})

    def run_signed(self,ticket,**other):
        args=dict(root=self.root,destination=self.output,ticket=ticket,
                  public_pin=self.pin,expected_owner=7,job_id=self.job)
        args.update(other)
        return j.clone_signed_fake(**args)

    def reject(self,ticket,**other):
        with self.assertRaises((j.J10Denied,FakeRecoveryDenied)):
            self.run_signed(ticket,**other)
        self.assertFalse(self.output.exists())

    def test_01_real_rsa_signed_wal_media_vault_copy(self):
        self.publish()
        r=self.run_signed(self.sign())
        self.assertIs(r["clinical_restore_permitted"],False)
        self.assertEqual(r["fake_destination"],"isolated-recovery")
        with closing(sqlite3.connect(str(self.output/"snapshot.db"))) as db:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone(),("ok",))
            self.assertEqual(db.execute("SELECT v FROM fake_truth").fetchone(),("COMMITTED_WAL",))
        self.assertFalse((self.output/"snapshot.db-wal").exists())
        for name in ("license_fake.bin","media-fake/scan.fake","media-fake/invoice.fake"):
            self.assertEqual((self.output/name).read_bytes(),(self.inputs/name).read_bytes())

    def test_02_changed_signed_body_rejected(self):
        self.publish()
        payload=json.loads(self.sign())
        payload["claims"]["owner"]=8
        self.reject(j.canonical(payload))
        self.assertFalse((self.root/"consumed-nonces").exists())

    def test_03_other_rsa_pin_rejected(self):
        self.publish()
        other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        pub=other.public_key().public_bytes(serialization.Encoding.PEM,
                                             serialization.PublicFormat.SubjectPublicKeyInfo)
        self.reject(self.sign(),public_pin=pub)

    def test_04_expired_or_not_yet_issued(self):
        self.publish()
        now=int(time.time())
        self.reject(self.sign(issued=now-140,expires=now-1))
        self.reject(self.sign(issued=now+20,expires=now+60))

    def test_05_wrong_owner_or_job_rejected(self):
        self.publish()
        ticket=self.sign()
        self.reject(ticket,expected_owner=8)
        self.reject(ticket,expected_owner=True)
        self.reject(ticket,job_id="f"*32)

    def test_06_wrong_signed_purpose_rejected(self):
        self.publish()
        self.reject(self.sign(purpose="REAL_CLINICAL_RESTORE"))
        self.reject(self.sign(owner=8))

    def test_07_nonce_replay_after_output_deletion_rejected(self):
        self.publish()
        token=self.sign(nonce="f"*32)
        self.run_signed(token)
        shutil.rmtree(self.output)
        with self.assertRaisesRegex(j.J10Denied,"NONCE_REPLAY_DENIED"):
            self.run_signed(token)

    def test_08_partial_restore_failure_preserves_current_and_burns_nonce(self):
        import backend.services.legacy_migration_safe_restore_lab_v15 as old
        self.publish()
        ticket=self.sign(nonce="e"*32)
        before=read_fake_current(self.root,request_owner=7,expected_owner=7)[1]
        def fake_failure(_src,target):
            target.mkdir()
            (target/"partial").write_bytes(b"FAKE")
            raise OSError("J10_INTERRUPTED")
        with patch.object(old.shutil,"copytree",side_effect=fake_failure):
            with self.assertRaisesRegex(OSError,"J10_INTERRUPTED"):
                self.run_signed(ticket)
        self.assertFalse(self.output.exists())
        self.assertEqual(before,read_fake_current(self.root,request_owner=7,expected_owner=7)[1])
        with self.assertRaisesRegex(j.J10Denied,"NONCE_REPLAY_DENIED"):
            self.run_signed(ticket)

    def test_09_corrupt_media_denied_before_nonce(self):
        self.publish()
        ticket=self.sign()
        generation,_=read_fake_current(self.root,request_owner=7,expected_owner=7)
        (generation/"media-fake/scan.fake").write_bytes(b"FORGED")
        self.reject(ticket)
        self.assertFalse((self.root/"consumed-nonces").exists())

    def test_10_generation_changed_denies_old_ticket(self):
        self.publish()
        old=self.sign()
        self.cn.execute("UPDATE fake_truth SET v='NEW_COMMITTED_WAL'")
        self.cn.commit()
        self.publish()
        with self.assertRaisesRegex(j.J10Denied,"SIGNED_MANIFEST_MISMATCH"):
            self.run_signed(old)

    def test_11_root_and_flag_denied(self):
        self.publish()
        ticket=self.sign()
        nested=self.root/"lot05j_fake_nested"
        nested.mkdir()
        self.reject(ticket,root=nested)
        with patch.dict(os.environ,{j.FLAG:"0"}):
            self.reject(ticket)

    def test_12_occupied_destination_never_replaced(self):
        self.publish()
        self.output.mkdir()
        marker=self.output/"keep"
        marker.write_bytes(b"ORIGINAL")
        with self.assertRaisesRegex(j.J10Denied,"NEW_ISOLATED_DESTINATION_REQUIRED"):
            self.run_signed(self.sign())
        self.assertEqual(marker.read_bytes(),b"ORIGINAL")

    def test_13_duplicate_json_and_malformed_ticket_denied(self):
        self.publish()
        t=json.loads(self.sign())
        d=(b'{"claims":'+j.canonical(t["claims"])+b',"claims":'+
           j.canonical(t["claims"])+b',"signature":"'+t["signature"].encode("ascii")+b'"}')
        self.reject(d)
        self.reject(b"NOT-A-TICKET")

    def test_14_ledger_symlink_guard(self):
        self.publish()
        token=self.sign()
        ledger=self.root/"consumed-nonces"
        ledger.mkdir()
        original=Path.is_symlink
        with patch.object(Path,"is_symlink",lambda path:path==ledger or original(path)):
            with self.assertRaisesRegex(j.J10Denied,"LEDGER_REDIRECTED"):
                self.run_signed(token)

if __name__=="__main__":
    unittest.main(verbosity=2)
