import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class FacadDcMapTests(unittest.TestCase):
    def test_mapping_reports_label_candidate_and_unmapped(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            ceph = tmp_path / "Ceph"
            ceph.mkdir()
            (ceph / "Demo.cph").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<Facad><cephfile><name>Demo</name><AnalysisType>Lateral</AnalysisType><ceph_set>
<ceph_calc><name>SNA</name><norm>82±2</norm></ceph_calc>
<ceph_calc><name>ML/FH</name><norm>25±4</norm></ceph_calc>
<ceph_calc><name>Unknown</name><norm>1±1</norm></ceph_calc>
</ceph_set></cephfile></Facad>""", encoding="utf-8")
            reg = {
                "profiles": {
                    "Demo": {
                        "facad_filename": "Demo.cph",
                        "mappings": {
                            "SNA": {"dc_id": "M_SNA_DEG_V1", "status": "CANONICAL_LABEL_MATCH"},
                            "ML/FH": {"dc_id": "M_FH_GOME_DEG_V1", "status": "CANDIDATE_GEOMETRY_REVIEW"},
                        },
                    }
                }
            }
            rp = tmp_path / "r.json"
            rp.write_text(json.dumps(reg), encoding="utf-8")
            contract = tmp_path / "contract.json"
            contract.write_text(json.dumps({"measurements": [
                {"measurement_id": "M_SNA_DEG_V1"},
                {"measurement_id": "M_FH_GOME_DEG_V1"},
            ]}), encoding="utf-8")
            out = tmp_path / "out.json"
            subprocess.run([
                sys.executable,
                "audit/cephalo_lot08_facad_dc_map.py",
                "--ceph-dir", str(ceph),
                "--registry", str(rp),
                "--dc-contract", str(contract),
                "--out", str(out),
            ], check=True)
            data = json.loads(out.read_text(encoding="utf-8"))["profiles"]["Demo"]
            self.assertEqual(data["facad_measurement_count"], 3)
            self.assertEqual(data["counts"], {
                "CANONICAL_LABEL_MATCH": 1,
                "CANDIDATE_GEOMETRY_REVIEW": 1,
                "UNMAPPED": 1,
            })

    def test_mapping_rejects_unknown_dc_id(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            ceph = tmp_path / "Ceph"
            ceph.mkdir()
            (ceph / "Demo.cph").write_text(
                """<?xml version="1.0" encoding="UTF-8"?><Facad><cephfile><name>Demo</name><ceph_set><ceph_calc><name>SNA</name><norm>82±2</norm></ceph_calc></ceph_set></cephfile></Facad>""",
                encoding="utf-8",
            )
            reg = {
                "profiles": {
                    "Demo": {
                        "facad_filename": "Demo.cph",
                        "mappings": {
                            "SNA": {"dc_id": "M_MISSING", "status": "CANONICAL_LABEL_MATCH"}
                        },
                    }
                }
            }
            rp = tmp_path / "r.json"
            rp.write_text(json.dumps(reg), encoding="utf-8")
            contract = tmp_path / "contract.json"
            contract.write_text(json.dumps({"measurements": []}), encoding="utf-8")
            out = tmp_path / "out.json"
            proc = subprocess.run([
                sys.executable,
                "audit/cephalo_lot08_facad_dc_map.py",
                "--ceph-dir", str(ceph),
                "--registry", str(rp),
                "--dc-contract", str(contract),
                "--out", str(out),
            ], capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Unknown dc_id", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
