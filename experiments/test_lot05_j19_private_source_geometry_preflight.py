"""Synthetic J19 source geometry/collision tests; never private data."""
import sys,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import lot05_j19_private_source_geometry_preflight as m
from test_lot05_j17_private_manifest_preflight import fixture
class TestJ19(unittest.TestCase):
    def setup_source(self,root,extra=""):
        for split in ("train","val","test"):(root/split).mkdir()
        p=root/"train"/"1001.txt";p.write_text("17 0.5 0.5 0.1 0.1\n"+extra)
        return {("train","1001"):p}
    def test_unique_witness_staging_blocked(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);inv=self.setup_source(root)
            with patch.object(m,"labels_inventory",return_value=inv):r=m.audit(fixture(),root,b"synthetic")
            self.assertEqual(r["active_witnesses_checked"],1)
            self.assertFalse(r["staging_performed"])
    def test_collision_is_reported_without_modifying_source(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);inv=self.setup_source(root,"16 0.2 0.2 0.1 0.1\n")
            before=inv[("train","1001")].read_bytes()
            with patch.object(m,"labels_inventory",return_value=inv):r=m.audit(fixture(),root)
            self.assertEqual(r["source_target_collision_files"],1)
            self.assertEqual(inv[("train","1001")].read_bytes(),before)
    def test_missing_bbox_fails(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);inv=self.setup_source(root)
            d=fixture();d["active_permanent"][0]["decision"]["expected_bbox"]=[.4,.5,.1,.1]
            with patch.object(m,"labels_inventory",return_value=inv):
                with self.assertRaises(ValueError):m.audit(d,root)
    def test_source_hash_mismatch_fails(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);inv=self.setup_source(root)
            with patch.object(m,"labels_inventory",return_value=inv):
                with self.assertRaises(ValueError):m.audit(fixture(),root,b"wrong")
if __name__=="__main__":unittest.main()
