"""Synthetic J20 source-availability and no-staging tests."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from test_lot05_j17_private_manifest_preflight import fixture
from lot05_j20_private_source_qa import verify
class J20Tests(unittest.TestCase):
    def test_missing_source_blocks(self):
        r=verify(fixture(),Path("/nonexistent-private-source"),b"synthetic")
        self.assertEqual(r["status"],"BLOCKED_ACADEMIC_SOURCE_LABELS_UNAVAILABLE")
        self.assertFalse(r["source_geometry_verified"])
        self.assertFalse(r["staging_performed"])
    def test_bad_source_manifest_hash_blocks(self):
        with self.assertRaises(ValueError):verify(fixture(),None,b"wrong")
    def test_primary_remains_blocked(self):
        r=verify(fixture(),None)
        self.assertEqual(r["primary_blocked_count"],1)
        self.assertFalse(r["training_authorized"])
if __name__=="__main__":unittest.main()
