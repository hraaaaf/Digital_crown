"""J10B actual SQLCipher committed WAL and crash tests (no clinical imports)."""
import importlib.util, os, secrets, sqlite3, subprocess, sys, tempfile, unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from sqlcipher3 import dbapi2 as cipher
F=Path(__file__).parent/"fixtures"/"lot05j10b_sqlcipher_multicomponent_lab.py"
spec=importlib.util.spec_from_file_location("j10b_offline",F); lab=importlib.util.module_from_spec(spec); spec.loader.exec_module(lab)
class NativeCipherRecovery(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="lot05j10b_fake_"); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.inputs=self.root/"inputs"; self.inputs.mkdir(); (self.inputs/"media-fake").mkdir()
        for p,data in (("media-fake/scan.fake",b"SCAN-FAKE"),("media-fake/invoice.fake",b"INVOICE-FAKE"),("license_fake.bin",b"VAULT-FAKE")):
            (self.inputs/p).write_bytes(data)
        self.key=secrets.token_hex(32); self.source=self.inputs/"clinical_fake.db"; self.c=lab.dbopen(self.source,self.key); self.addCleanup(self.c.close)
        self.assertEqual(self.c.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower(),"wal")
        self.c.execute("PRAGMA wal_autocheckpoint=0"); self.c.execute("CREATE TABLE truth(v TEXT)"); self.c.execute("INSERT INTO truth VALUES ('WAL-COMMITTED')"); self.c.commit()
        self.assertGreater(Path(str(self.source)+"-wal").stat().st_size,0)
        p=patch.dict(os.environ,{lab.FLAG:"1"}); p.start(); self.addCleanup(p.stop)
    def do(self,fail_at=None): return lab.publish(self.root,self.key,fail_at)
    def check(self): return lab.verify(self.root,self.key)
    def test_01_sqlcipher_encrypted_committed_wal_media_vault(self):
        self.do(); root,rec=self.check()
        with closing(lab.dbopen(root/"snapshot.db",self.key)) as db:
            self.assertEqual(db.execute("SELECT v FROM truth").fetchone(),("WAL-COMMITTED",))
        self.assertNotIn(b"WAL-COMMITTED",(root/"snapshot.db").read_bytes())
        self.assertFalse((root/"snapshot.db-wal").exists())
        self.assertEqual(set(rec["manifest"]),set(lab.COMPONENTS))
    def test_02_wrong_key_rejected(self):
        self.do()
        with self.assertRaises((lab.Refused,cipher.DatabaseError)): lab.verify(self.root,secrets.token_hex(32))
    def test_03_tampered_media_denied(self):
        self.do(); folder,_=self.check(); (folder/"media-fake/scan.fake").write_bytes(b"FAKE-TAMPER")
        with self.assertRaises(lab.Refused): self.check()
    def test_04_interrupt_after_db_no_publish(self):
        with self.assertRaisesRegex(lab.Refused,"FAULT_AFTER_DB"): self.do("after_db")
        self.assertFalse((self.root/"CURRENT.json").exists())
        self.assertFalse(list((self.root/"generations").glob(".stage_*")))
    def test_05_interrupt_after_media_old_pointer_retained(self):
        self.do(); before=self.check()[1]
        with self.assertRaisesRegex(lab.Refused,"FAULT_AFTER_MEDIA"): self.do("after_media")
        self.assertEqual(before,self.check()[1])
    def test_06_interrupt_after_generation_old_pointer_retained(self):
        self.do(); before=self.check()[1]
        with self.assertRaisesRegex(lab.Refused,"FAULT_AFTER_GENERATION"): self.do("after_generation")
        self.assertEqual(before,self.check()[1])
    def test_07_abrupt_subprocess_exit_keeps_old_pointer(self):
        self.do(); before=self.check()[1]
        child=subprocess.run([sys.executable,"-B",str(F),str(self.root),self.key],
                             capture_output=True,text=True,timeout=45,env=dict(os.environ))
        self.assertEqual(child.returncode,73,child.stderr[-2000:])
        self.assertEqual(before,self.check()[1]); self.assertTrue(list((self.root/"generations").glob(".stage_*")))
    def test_08_next_generation_sees_new_wal_commit(self):
        self.do(); oldroot,old=self.check()
        self.c.execute("UPDATE truth SET v='SECOND-COMMITTED'"); self.c.commit(); self.do(); newroot,new=self.check()
        self.assertNotEqual(old["generation"],new["generation"])
        with closing(lab.dbopen(newroot/"snapshot.db",self.key)) as db: self.assertEqual(db.execute("SELECT v FROM truth").fetchone(),("SECOND-COMMITTED",))
        with closing(lab.dbopen(oldroot/"snapshot.db",self.key)) as db: self.assertEqual(db.execute("SELECT v FROM truth").fetchone(),("WAL-COMMITTED",))
    def test_09_wrong_flag_and_nested_root_denied(self):
        with patch.dict(os.environ,{lab.FLAG:"0"}):
            with self.assertRaises(lab.Refused): self.do()
        nest=self.root/"lot05j10b_fake_nested"; nest.mkdir()
        with self.assertRaises(lab.Refused): lab.publish(nest,self.key)
    def test_10_linked_input_media_denied(self):
        path=self.inputs/"media-fake/scan.fake"; orig=Path.is_symlink
        with patch.object(Path,"is_symlink",lambda p:p==path or orig(p)):
            with self.assertRaises(lab.Refused): self.do()
if __name__=="__main__": unittest.main(verbosity=2)
