import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / 'docs' / 'audits' / 'schemas' / 'ortho_lot08_tweed_facad_gap_resolution_v1.json'

class TweedFacadGapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SCHEMA.read_text(encoding='utf-8'))

    def test_wits_is_vendor_variant_not_strict_jacobson(self):
        row = self.data['resolutions']['Wits']['dc_resolution']
        self.assertEqual(row['status'], 'FACAD_VENDOR_VARIANT_SOURCE_LOCKED__JACOBSON_STRICT_EQUIVALENCE_FORBIDDEN')
        self.assertFalse(row['canonical_wits_profile_promotion'])
        self.assertFalse(row['legacy_alias_allowed'])
        self.assertFalse(row['runtime_activation'])
        self.assertEqual(self.data['resolutions']['Wits']['facad_definition']['projection_vector_order'], ['B', 'A'])
        self.assertEqual(self.data['resolutions']['Wits']['facad_definition']['line_direction'], 'OLp_to_OLa')

    def test_facad_occlusal_line_is_explicit_and_manual_posteriorly(self):
        c = self.data['facad_constructions']
        self.assertEqual(c['OLa']['refs'], ['Is', 'Ii'])
        self.assertEqual(c['OLa']['calc_type'], 'Mid-point')
        self.assertEqual(c['OLp']['acquisition'], 'MANUAL_VENDOR_MARKER')
        self.assertEqual(c['OL']['refs'], ['OLp', 'OLa'])
        self.assertEqual(c['OL']['argument_order'], ['OLp', 'OLa'])
        self.assertEqual(c['OL']['direction'], 'OLp_to_OLa')

    def test_olfh_cannot_claim_strict_downs_or_tweed_membership(self):
        row = self.data['resolutions']['OL/FH']['dc_resolution']
        self.assertFalse(row['canonical_tweed_profile_promotion'])
        self.assertFalse(row['canonical_downs_profile_promotion'])
        self.assertFalse(row['runtime_activation'])
        self.assertTrue(self.data['safety_rules']['no_historical_tweed_membership_inference'])

    def test_legacy_occlusal_aliases_are_forbidden(self):
        self.assertTrue(self.data['safety_rules']['no_alias_to_legacy_occ_ant_post'])
        self.assertTrue(self.data['safety_rules']['no_runtime_activation_without_explicit_olp'])

    def test_functional_vs_bisected_plane_claim_has_explicit_sources(self):
        evidence = self.data["scientific_authorities"]["wits_functional_plane_corrobation"]
        ids = {item["id"] for item in evidence["sources"]}
        self.assertIn("PMC4072364", ids)
        self.assertIn("THAYER_1990", ids)
        self.assertIn("vendor bisected-plane variant", evidence["conclusion"])

    def test_vendor_norms_and_numeric_parity_remain_gated(self):
        self.assertTrue(self.data['safety_rules']['no_facad_norm_runtime_classification'])
        self.assertTrue(self.data['safety_rules']['no_numeric_parity_claim_without_same_trace_export'])

if __name__ == '__main__':
    unittest.main()