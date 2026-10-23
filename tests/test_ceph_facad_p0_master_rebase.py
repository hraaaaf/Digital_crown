"""Safety and reproducibility tests for exact-commit P0 static-rebase audit."""
import copy
import json
import unittest

from scripts.audit_ceph_facad_p0_master_rebase import (
    AuditError, MATRIX, OLD_MASTER, PINNED_MASTER, REQUIRED_EVIDENCE,
    SOURCE_BLOBS, SCHEMA, examine, render_md,
)


def source_fixture(matrix):
    data = {path: "" for path in SOURCE_BLOBS}
    for row in matrix["toolbar"]:
        if row["digital_crown_code_path"] is not None:
            data[row["digital_crown_code_path"]] += "\n" + row["digital_crown_source_needle"]
    data["backend/services/cephalo_runtime_chain.py"] = (
        '{"steiner": project_steiner_static_protocol('
        '\n"tweed_merrifield": project_tweed_merrifield_protocol('
    )
    return data


class CEPHFacP0RebaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.source = source_fixture(cls.matrix)
        cls.report = examine(cls.matrix, cls.source)

    def test_three_level_count_without_parity_inflation(self):
        r = self.report
        self.assertEqual(r["schema"], SCHEMA)
        self.assertEqual((r["counts"]["vendor_menus_documented"], r["counts"]["toolbar_total"], r["counts"]["workflow_total"]), (9, 30, 7))
        self.assertEqual((r["counts"]["toolbar_code_string_matched_only"], r["counts"]["toolbar_not_proven"]), (9, 21))
        self.assertEqual(r["counts"]["workflow_source_paths_present"], 7)
        self.assertEqual(r["counts"]["workflow_e2e_parity_verified"], 0)
        self.assertEqual(r["counts"]["toolbar_vendor_actions_verified"], 0)

    def test_no_clinical_promotion_no_roadmap_inflation(self):
        r = self.report
        self.assertFalse(r["clinical_go"])
        self.assertFalse(r["deployment_authorized"])
        self.assertFalse(r["merge_authorized"])
        self.assertEqual((r["roadmap_before"], r["roadmap_after"]), ("41/99", "41/99"))
        self.assertEqual(r["facad_storage_isolation"], "UNVERIFIED")
        self.assertIn("NO-GO", render_md(r))
        self.assertEqual(r["master_protocol_profiles_confirmed_in_runtime_chain"], {"steiner": True, "tweed_merrifield": True})

    def test_evidence_narrowness_and_no_individual_patient_data(self):
        serialized = json.dumps(self.report)
        self.assertNotIn('"case_id"', serialized)
        self.assertNotIn('"image_path"', serialized)
        self.assertNotIn('"coordinates"', serialized)
        self.assertEqual({x["parity_status"] for x in self.report["toolbar"]}, {"NOT_PROVEN"})
        self.assertEqual({x["parity_status"] for x in self.report["workflows"]}, {"NOT_PROVEN"})

    def test_mutated_parent_source_baseline_rejected(self):
        bad = copy.deepcopy(self.matrix)
        bad["digital_crown_base_sha"] = PINNED_MASTER
        with self.assertRaises(AuditError):
            examine(bad, self.source)

    def test_duplicate_toolbar_id_rejected(self):
        bad = copy.deepcopy(self.matrix)
        bad["toolbar"][1]["id"] = bad["toolbar"][0]["id"]
        with self.assertRaises(AuditError):
            examine(bad, self.source)

    def test_reclassifying_vendor_action_as_tested_rejected(self):
        bad = copy.deepcopy(self.matrix)
        bad["toolbar"][0]["vendor_action_verdict"] = "TESTED"
        with self.assertRaises(AuditError):
            examine(bad, self.source)

    def test_forced_clinical_and_equivalence_promotion_rejected(self):
        for field in ("clinical_release", "facad_to_dc_equivalence_verified", "numeric_parity_verified"):
            bad = copy.deepcopy(self.matrix)
            bad["toolbar"][0][field] = True
            with self.subTest(field=field), self.assertRaises(AuditError):
                examine(bad, self.source)

    def test_missing_code_needle_degrades_not_proven_instead_of_pass(self):
        sources = dict(self.source)
        path = self.matrix["toolbar"][0]["digital_crown_code_path"]
        sources[path] = sources[path].replace(self.matrix["toolbar"][0]["digital_crown_source_needle"], "")
        r = examine(self.matrix, sources)
        self.assertEqual(r["counts"]["toolbar_code_string_matched_only"], 8)
        self.assertEqual(r["counts"]["toolbar_not_proven"], 22)
        self.assertEqual(r["toolbar"][0]["source_status"], "NOT_PROVEN")

    def test_workflow_missing_required_source_or_evidence_rejected(self):
        bad = copy.deepcopy(self.matrix)
        bad["workflows"][0]["dc_code_paths"].append("frontend/imaginary.tsx")
        with self.assertRaises(AuditError):
            examine(bad, self.source)
        bad = copy.deepcopy(self.matrix)
        bad["workflows"][0]["required_evidence"] = list(REQUIRED_EVIDENCE - {"DC_AUTHENTICATED_BEFORE_AFTER"})
        with self.assertRaises(AuditError):
            examine(bad, self.source)

    def test_vendor_d3_and_parent_gate_regressions_rejected(self):
        bad = copy.deepcopy(self.matrix)
        bad["gates"]["vendor_numeric_parity_verified"] = True
        with self.assertRaises(AuditError):
            examine(bad, self.source)
        blocked = [r for r in self.report["toolbar"] if r["vendor_mutation_gate"] == "BLOCKED"]
        self.assertGreater(len(blocked), 0)
        self.assertTrue(all(not r["clinical_go"] for r in blocked))

if __name__ == "__main__":
    unittest.main()
