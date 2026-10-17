"""Nonclinical source identity and fail-closed tests only."""
import copy
import unittest
from scripts.cephalo_r23g9_verify_aariz_matrix import (
    check_guardrails, read, SOURCE, verify,
)


class GoldsetPreflightTests(unittest.TestCase):
    def test_exact_source_inventory(self):
        report = verify()
        self.assertEqual(len(report["rows"]), 33)
        self.assertEqual(report["counts"]["clinically_validated_atlas_measurements"], 0)

    def test_clinical_promotion_rejected(self):
        changed = copy.deepcopy(read(SOURCE))
        changed["clinical_release"] = True
        with self.assertRaises(ValueError):
            check_guardrails(changed)
        changed["clinical_release"] = False
        changed["rows"][5]["active_focus_authorized"] = True
        with self.assertRaises(ValueError):
            check_guardrails(changed)

    def test_alias_promotion_rejected(self):
        changed = copy.deepcopy(read(SOURCE))
        changed["semantic_aliasing_authorized"] = True
        with self.assertRaises(ValueError):
            check_guardrails(changed)

    def test_strict_identity_missing_and_order_stable(self):
        report = verify()
        rows = {x["order"]: x for x in report["rows"]}
        self.assertIn("Po_anatomic", rows[31]["identities_not_in_strict_aariz_mapping"])
        self.assertIn("Pt_Ricketts", rows[27]["identities_not_in_strict_aariz_mapping"])
        self.assertIn("PR_Ricketts_PTV", rows[23]["identities_not_in_strict_aariz_mapping"])
        self.assertIn("Pm_Ricketts", rows[29]["identities_not_in_strict_aariz_mapping"])
        self.assertEqual(rows[6]["identities_not_in_strict_aariz_mapping"], [])


if __name__ == "__main__":
    unittest.main()
