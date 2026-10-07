import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = "audit/cephalo_lot08_facad_dc_map.py"


def _run(tmp_path, ceph_xml, registry, contract, protocol_profile=None):
    ceph = tmp_path / "Ceph"
    ceph.mkdir()
    (ceph / "Demo.cph").write_text(ceph_xml, encoding="utf-8")
    rp = tmp_path / "registry.json"
    rp.write_text(json.dumps(registry), encoding="utf-8")
    cp = tmp_path / "contract.json"
    cp.write_text(json.dumps(contract), encoding="utf-8")
    out = tmp_path / "out.json"
    cmd = [
        sys.executable, SCRIPT,
        "--ceph-dir", str(ceph),
        "--registry", str(rp),
        "--dc-contract", str(cp),
        "--out", str(out),
    ]
    if protocol_profile is not None:
        pp = tmp_path / "profile.json"
        pp.write_text(json.dumps(protocol_profile), encoding="utf-8")
        cmd += ["--protocol-profile", str(pp)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc, out


class FacadDcMapTests(unittest.TestCase):
    def test_mapping_reports_all_status_buckets(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<Facad><cephfile><name>Demo</name><ceph_set>
<ceph_calc><name>SNA</name><norm>82±2</norm></ceph_calc>
<ceph_calc><name>ML/FH</name><norm>25±4</norm></ceph_calc>
<ceph_calc><name>REL</name><norm>0±2</norm></ceph_calc>
<ceph_calc><name>BLOCK</name><norm>0</norm></ceph_calc>
<ceph_calc><name>Unknown</name><norm>1±1</norm></ceph_calc>
</ceph_set></cephfile></Facad>"""
            registry = {
                "profiles": {
                    "Demo": {
                        "facad_filename": "Demo.cph",
                        "mappings": {
                            "SNA": {"dc_id": "M_SNA", "status": "CANONICAL_LABEL_MATCH"},
                            "ML/FH": {"dc_id": "M_FMA", "status": "CANDIDATE_GEOMETRY_REVIEW"},
                            "REL": {"dc_relationship_id": "REL_1", "status": "EXISTING_DERIVED_RELATIONSHIP"},
                            "BLOCK": {
                                "status": "BLOCKED_EXACT_LANDMARK",
                                "required_identity": "MS_Steiner",
                                "forbidden_aliases": ["Cm"],
                            },
                        },
                    }
                }
            }
            contract = {"measurements": [{"measurement_id": "M_SNA"}, {"measurement_id": "M_FMA"}]}
            profile = {"derived_relationships": [{"relationship_id": "REL_1"}]}
            proc, out = _run(tmp_path, xml, registry, contract, profile)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))["profiles"]["Demo"]
            self.assertEqual(data["counts"], {
                "CANONICAL_LABEL_MATCH": 1,
                "CANDIDATE_GEOMETRY_REVIEW": 1,
                "EXISTING_DERIVED_RELATIONSHIP": 1,
                "BLOCKED_EXACT_LANDMARK": 1,
                "UNMAPPED": 1,
            })

    def test_mapping_rejects_unknown_dc_id(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            xml = """<?xml version="1.0" encoding="UTF-8"?><Facad><cephfile><name>Demo</name><ceph_set><ceph_calc><name>SNA</name><norm>82±2</norm></ceph_calc></ceph_set></cephfile></Facad>"""
            registry = {"profiles": {"Demo": {"facad_filename": "Demo.cph", "mappings": {"SNA": {"dc_id": "M_MISSING", "status": "CANONICAL_LABEL_MATCH"}}}}}
            proc, _ = _run(tmp_path, xml, registry, {"measurements": []})
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Unknown dc_id", proc.stdout + proc.stderr)

    def test_relationship_mapping_must_exist_in_protocol_profile(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            xml = """<?xml version="1.0" encoding="UTF-8"?><Facad><cephfile><name>Demo</name><ceph_set><ceph_calc><name>REL</name><norm>0±2</norm></ceph_calc></ceph_set></cephfile></Facad>"""
            registry = {"profiles": {"Demo": {"facad_filename": "Demo.cph", "mappings": {"REL": {"dc_relationship_id": "REL_MISSING", "status": "EXISTING_DERIVED_RELATIONSHIP"}}}}}
            proc, _ = _run(tmp_path, xml, registry, {"measurements": []}, {"derived_relationships": []})
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("Unknown dc_relationship_id", proc.stdout + proc.stderr)

    def test_blocked_mapping_requires_forbidden_aliases(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            xml = """<?xml version="1.0" encoding="UTF-8"?><Facad><cephfile><name>Demo</name><ceph_set><ceph_calc><name>BLOCK</name><norm>0</norm></ceph_calc></ceph_set></cephfile></Facad>"""
            registry = {"profiles": {"Demo": {"facad_filename": "Demo.cph", "mappings": {"BLOCK": {"status": "BLOCKED_EXACT_LANDMARK", "required_identity": "MS_Steiner"}}}}}
            proc, _ = _run(tmp_path, xml, registry, {"measurements": []})
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("missing forbidden_aliases", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
