import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = "audit/cephalo_lot08_facad_dc_map.py"
ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_dc_unmapped_backlog_v1.json"
WORKFLOW = ROOT / ".github" / "workflows" / "facad-314-dc-protocol-map.yml"


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


class DownsFacadHighReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(BACKLOG.read_text(encoding="utf-8"))
        cls.downs = cls.data["profiles"]["Downs"]
        cls.rows = {row["facad_label"]: row for row in cls.downs["resolved_items"]}

    def test_downs_five_gaps_are_dispositioned_and_global_backlog_is_26(self):
        self.assertEqual(self.downs["unmapped"], [])
        self.assertEqual(set(self.rows), {"Convexity", "A-B plane", "OL/FH", "ILi/OL", "Is to A-Pog"})
        self.assertEqual(self.data["high_review_progress"]["Downs"]["remaining_unmapped"], 0)
        self.assertEqual(self.data["totals"]["unmapped_items"], 26)

    def test_downs_convexity_and_ab_plane_remain_signed_parity_gated(self):
        convexity = self.rows["Convexity"]
        ab_plane = self.rows["A-B plane"]
        self.assertEqual(convexity["facad_definition"]["refs"], ["N", "A", "A", "Pog"])
        self.assertEqual(ab_plane["facad_definition"]["refs"], ["A", "B", "N", "Pog"])
        self.assertIn("SIGNED_PARITY_GATED", convexity["resolution"])
        self.assertIn("SIGNED_PARITY_GATED", ab_plane["resolution"])
        self.assertFalse(convexity["runtime_activation"])
        self.assertFalse(ab_plane["runtime_activation"])

    def test_downs_occlusal_cant_does_not_claim_strict_olp_semantics(self):
        row = self.rows["OL/FH"]
        self.assertEqual(row["facad_definition"]["refs"], ["FH", "OL"])
        self.assertIn("STRICT_OLP_SEMANTICS_UNPROVEN", row["resolution"])
        self.assertFalse(row["runtime_activation"])

    def test_downs_ili_ol_preserves_raw_angle_and_complement_relation(self):
        row = self.rows["ILi/OL"]
        self.assertEqual(row["facad_definition"]["refs"], ["Iia", "Ii", "OLp", "OLa"])
        self.assertEqual(row["facad_definition"]["norm"], "75.5±3.5")
        self.assertEqual(row["candidate_downs_relation"], "90_deg_minus_raw_angle")
        self.assertIn("COMPLEMENT", row["resolution"])
        self.assertFalse(row["runtime_activation"])

    def test_downs_upper_incisor_apog_does_not_alias_ricketts(self):
        row = self.rows["Is to A-Pog"]
        self.assertEqual(row["facad_definition"]["refs"], ["Pog", "A", "Is"])
        self.assertEqual(row["existing_geometry_family_reference"], "M_RICKETTS_U1_APOG_PROTRUSION_MM_V1")
        self.assertFalse(row["direct_alias_allowed"])
        self.assertFalse(row["runtime_activation"])

    def test_downs_vendor_evidence_is_pinned(self):
        evidence = self.data["high_review_progress"]["Downs"]["evidence"]
        self.assertEqual(evidence["inventory_run_id"], 37596906703)
        self.assertEqual(evidence["artifact_id"], 11470928482)
        self.assertEqual(
            evidence["facad_profile_sha256"],
            "3415d02e655c5f4cb6b1e0ef466a0f75fa1947f971b3b200568f8f00925625de",
        )
        self.assertEqual(evidence["facad_profile_measurement_count"], 10)

    def test_downs_workflow_fails_closed_on_profile_sha_drift(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("Verify pinned Downs profile bytes", workflow)
        self.assertIn(
            "3415d02e655c5f4cb6b1e0ef466a0f75fa1947f971b3b200568f8f00925625de",
            workflow,
        )
        self.assertIn("Get-FileHash -Algorithm SHA256", workflow)
        self.assertIn("Downs.cph SHA256 drift", workflow)


if __name__ == "__main__":
    unittest.main()
