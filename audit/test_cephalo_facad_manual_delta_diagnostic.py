"""Offline FACAD/DC differences: synthetic candidates ONLY, not clinical parity."""
import copy
import tempfile
import unittest
from pathlib import Path

from audit import cephalo_facad_manual_delta_diagnostic as d


class FacadManualDeltaFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.lock = d.source_lock()  # read actual committed source-lock contracts
        self.label = next(iter(self.lock["mapped"]))
        self.body = {
            "schema_version": d.INPUT_SCHEMA,
            "same_trace_case_id": "SYNTHETIC_TRACE_ONLY",
            "rows": [],
        }

    def candidate(self, label=None, order=1, target=d.TARGET_32F):
        return {
            "profile_target_id": target,
            "facad_order": order,
            "facad_label": label or self.label,
            "facad_value": "22.250",
            "facad_unit": "mm",
            "dc_measurement_id": "M_SYNTHETIC_TEST_V1",
            "dc_value": "22.125",
            "dc_unit": "mm",
            "geometry_identity_verified": True,
            "sign_orientation_verified": True,
            "rounding_verified": True,
        }

    def test_32_names_13_positions_7_forbidden(self):
        x = d.readiness_report()
        self.assertEqual(x["source_32f_label_count"], 32)
        self.assertEqual(x["source_13f_factor_positions"], list(range(1, 14)))
        self.assertFalse(x["source_13f_named_roster_independently_available"])
        self.assertEqual(len(x["sensitive_32f_no_direct_alias"]), 7)
        self.assertEqual(x["numeric_clinical_parity_rows"], 0)
        self.assertFalse(x["numeric_clinical_parity_proved"])

    def test_raw_candidate_difference_is_never_clinical_pass(self):
        self.body["rows"] = [self.candidate()]
        x = d.diagnostic(self.body)
        r = x["manual_candidate_delta_rows"][0]
        self.assertEqual(r["raw_decimal_delta_facad_minus_dc"], "0.125")
        self.assertEqual(r["status"], "RAW_MANUAL_DIFFERENCE_UNVERIFIED")
        self.assertFalse(r["clinical_parity_proved"])
        self.assertFalse(x["numeric_clinical_parity_proved"])

    def test_equal_numbers_still_not_clinical_parity(self):
        r = self.candidate()
        r["dc_value"] = r["facad_value"]
        self.body["rows"] = [r]
        x = d.diagnostic(self.body)
        self.assertEqual(x["manual_candidate_delta_rows"][0]["raw_decimal_delta_facad_minus_dc"], "0.000")
        self.assertEqual(x["numeric_clinical_parity_rows"], 0)

    def test_all_seven_sensitive_geometries_forbid_even_identical_values(self):
        for label, order in self.lock["seven"].items():
            with self.subTest(label=label):
                r = self.candidate(label, order)
                r["dc_value"] = r["facad_value"]
                self.body["rows"] = [r]
                output = d.diagnostic(self.body)["manual_candidate_delta_rows"][0]
                self.assertIn("SEVEN_SENSITIVE_DIRECT_ALIAS_FORBIDDEN", output["gates"])
                self.assertIsNone(output["raw_decimal_delta_facad_minus_dc"])

    def test_vendor_variants_outside_seven_block(self):
        candidates = [label for label, value in self.lock["resolved"].items()
                      if "FACAD_VENDOR" in value and label not in self.lock["seven"]]
        self.assertTrue(candidates)
        self.body["rows"] = [self.candidate(candidates[0])]
        x = d.diagnostic(self.body)["manual_candidate_delta_rows"][0]
        self.assertIn("VENDOR_VARIANT_REQUIRES_SEPARATE_GEOMETRY", x["gates"])
        self.assertIsNone(x["raw_decimal_delta_facad_minus_dc"])

    def test_thirteen_factors_are_not_silently_claimed_mapped(self):
        self.body["rows"] = [self.candidate("VendorNameUnknownHere", 1, d.TARGET_13F)]
        x = d.diagnostic(self.body)["manual_candidate_delta_rows"][0]
        self.assertIn("13F_NAMED_VENDOR_ROSTER_NOT_IN_THIS_SOURCE", x["gates"])
        self.assertIsNone(x["raw_decimal_delta_facad_minus_dc"])

    def test_missing_anatomical_sign_or_rounding_proof_abstains(self):
        for flag in ("geometry_identity_verified", "sign_orientation_verified", "rounding_verified"):
            with self.subTest(flag=flag):
                r = self.candidate()
                r[flag] = False
                self.body["rows"] = [r]
                self.assertIsNone(d.diagnostic(self.body)["manual_candidate_delta_rows"][0]
                                  ["raw_decimal_delta_facad_minus_dc"])

    def test_units_must_not_be_interchanged(self):
        r = self.candidate()
        r["dc_unit"] = "deg"
        self.body["rows"] = [r]
        x = d.diagnostic(self.body)["manual_candidate_delta_rows"][0]
        self.assertIn("UNIT_MISMATCH", x["gates"])
        self.assertIsNone(x["raw_decimal_delta_facad_minus_dc"])

    def test_unknown_roster_and_sensitive_orders_fail_closed(self):
        for row in (self.candidate("NOT_IN_CPH"), self.candidate("Mand len", 1)):
            with self.subTest(row=row):
                self.body["rows"] = [row]
                with self.assertRaises(ValueError):
                    d.diagnostic(self.body)

    def test_duplicate_names_positions_fail_closed(self):
        self.body["rows"] = [self.candidate(), self.candidate()]
        with self.assertRaises(ValueError):
            d.diagnostic(self.body)

    def test_nan_floats_locale_comma_and_exponents_fail_closed(self):
        for val in (2.0, "NaN", "Infinity", "1,25", "1e3", "1.123456789", ""):
            with self.subTest(val=val):
                r = self.candidate()
                r["facad_value"] = val
                self.body["rows"] = [r]
                with self.assertRaises(ValueError):
                    d.diagnostic(self.body)

    def test_unknown_identifying_fields_and_patient_name_fail_closed(self):
        self.body["patient_name"] = "DO_NOT_ACCEPT"
        with self.assertRaises(ValueError):
            d.diagnostic(self.body)
        del self.body["patient_name"]
        self.body["same_trace_case_id"] = "Robert Example / 850101-0010"
        with self.assertRaises(ValueError):
            d.diagnostic(self.body)

    def test_empty_safe_readiness_has_no_vendor_parity(self):
        self.body["rows"] = []
        out = d.diagnostic(self.body)
        self.assertFalse(out["vendor_source_data_read"])
        self.assertTrue(out["clinical_no_go"])
        self.assertEqual(out["manual_candidate_delta_rows"], [])

    def test_source_guard_detects_unsafe_seven_alias(self):
        original = d.read
        def unsafe(path):
            j = copy.deepcopy(original(path))
            if path == d.FINAL_SEVEN:
                j["resolutions"]["Mand len"]["dc"]["direct_alias_allowed"] = True
            return j
        from unittest.mock import patch
        with patch.object(d, "read", side_effect=unsafe):
            with self.assertRaises(ValueError):
                d.source_lock()

    def test_private_readiness_output_not_public(self):
        with tempfile.TemporaryDirectory(prefix="FACAD_SYNTHETIC_PRIVATE_") as root:
            report = Path(root) / "source_only.json"
            from unittest.mock import patch
            with patch("sys.argv", ["diagnostic", "--private-output", str(report)]):
                self.assertEqual(d.main(), 0)
            self.assertTrue(report.is_file())
            self.assertFalse(d.read(report)["numeric_clinical_parity_proved"])
            with patch("sys.argv", ["diagnostic", "--private-output", str(report)]):
                self.assertEqual(d.main(), 2)


if __name__ == "__main__":
    unittest.main()
