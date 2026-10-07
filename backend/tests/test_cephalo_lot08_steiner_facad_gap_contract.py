import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_steiner_facad_gap_resolution_v1.json"


class SteinerFacadGapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SCHEMA.read_text(encoding="utf-8"))

    def test_sline_requires_explicit_steiner_ms_and_forbids_silent_aliases(self):
        ms = self.data["identities"]["MS_Steiner"]
        self.assertEqual(ms["dc_alias_policy"]["Cm"], "FORBIDDEN_UNLESS_EQUIVALENCE_PROVEN")
        self.assertEqual(ms["dc_alias_policy"]["Sn_soft"], "FORBIDDEN")
        self.assertEqual(ms["dc_alias_policy"]["Prn"], "FORBIDDEN")
        self.assertEqual(ms["current_runtime_status"], "MISSING_EXACT_IDENTITY")\n        self.assertEqual(ms["vendor_to_historical_variant_equivalence"], "UNPROVEN")\n        self.assertTrue(self.data["safety_rules"]["no_midpoint_tangent_variant_equivalence_without_primary_proof"])
        self.assertTrue(self.data["safety_rules"]["missing_MS_must_fail_closed"])

    def test_sline_measurements_cannot_claim_runtime_parity(self):
        for key in ("Ls-SL", "Li-SL"):
            resolution = self.data["resolutions"][key]["dc_resolution"]
            self.assertFalse(resolution["runtime_activation"])
            self.assertEqual(resolution["sign_convention"], "UNOBSERVED_FOR_FACAD_RUNTIME_PARITY")
            self.assertEqual(resolution["required_new_identity"], "MS_STEINER_FACAD_TANGENT_POINT_V1")
            self.assertEqual(resolution["required_construction"], "SL_STEINER_POGSOFT_MS_V1")

    def test_iipog_is_derived_not_new_geometry(self):
        row = self.data["resolutions"]["Ii-Pog // NB"]
        self.assertEqual(row["facad_definition"]["calc_type"], "Sub")
        self.assertEqual(row["facad_definition"]["operands"], ["Ii-NB", "Pog-NB"])
        self.assertFalse(row["facad_definition"]["new_geometry"])
        self.assertFalse(row["dc_resolution"]["runtime_activation"])
        self.assertEqual(row["dc_resolution"]["status"], "DERIVED_RELATION_SOURCE_LOCKED__NUMERIC_EQUIVALENCE_GATED")\n        self.assertEqual(row["dc_resolution"]["dependency_geometry"]["facad_iil"], "Incisor inferior labial outline")\n        self.assertTrue(self.data["safety_rules"]["iinb_same_trace_numeric_parity_required"])

    def test_historical_primary_attribution_remains_gated(self):
        gate = self.data["historical_attribution"]
        self.assertEqual(gate["exact_primary_steiner_sline_publication_status"], "NOT_SOURCE_LOCKED_IN_THIS_COMPATIBILITY_LOT")
        self.assertFalse(gate["canonical_steiner_profile_promotion"])
        self.assertTrue(self.data["safety_rules"]["no_canonical_steiner_profile_promotion_without_primary_sline_source"])

    def test_vendor_norms_are_not_runtime_classification_authority(self):
        self.assertTrue(self.data["safety_rules"]["no_facad_norm_runtime_classification"])
        self.assertTrue(self.data["safety_rules"]["no_numeric_parity_claim_without_same_trace_export"])


if __name__ == "__main__":
    unittest.main()
