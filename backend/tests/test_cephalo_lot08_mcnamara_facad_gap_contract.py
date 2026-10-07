import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / 'docs' / 'audits' / 'schemas' / 'ortho_lot08_mcnamara_facad_gap_resolution_v1.json'

class McNamaraFacadGapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SCHEMA.read_text(encoding='utf-8'))

    def test_canonical_geometry_matches_are_explicit(self):
        self.assertEqual(self.data['resolutions']['Max-Mand diff']['dc']['measurement_id'], 'M_CO_GN_MINUS_CO_A_MM_V1')
        self.assertEqual(self.data['resolutions']['LAFH']['dc']['measurement_id'], 'M_ANS_ME_MM_V1')

    def test_incisisal_tip_variants_do_not_alias_surface_measurements(self):
        self.assertIn('STRICT_SURFACE_EQUIVALENCE_FORBIDDEN', self.data['resolutions']['Is-A']['dc']['status'])
        self.assertIn('STRICT_SURFACE_EQUIVALENCE_FORBIDDEN', self.data['resolutions']['Ii to A-Pog']['dc']['status'])
        self.assertTrue(self.data['safety_rules']['no_alias_incisisal_tip_variants_to_mcnamara_surface_measurements'])

    def test_nasolabial_vendor_variant_is_separate(self):
        row = self.data['resolutions']['Nasolabial']
        self.assertEqual(row['facad']['refs'], ['SN','MS','Ls'])
        self.assertIn('EQUIVALENCE_FORBIDDEN', row['dc']['status'])
        self.assertFalse(row['dc']['runtime_activation'])

    def test_lip_cant_vendor_variant_is_separate(self):
        row = self.data['resolutions']['Ls Cant']
        self.assertEqual(row['facad']['dependencies']['Ls-N'], 'Line(Ls,N)')
        self.assertEqual(row['facad']['dependencies']['NP'], 'Normal(FH,N)')
        self.assertIn('EQUIVALENCE_FORBIDDEN', row['dc']['status'])

    def test_signed_lower_incisor_vendor_semantics_are_preserved(self):
        self.assertTrue(self.data['resolutions']['Ii to A-Pog']['facad']['changeRightLeft'])
        self.assertTrue(self.data['safety_rules']['preserve_facad_changeRightLeft_for_ii_apog'])

    def test_runtime_and_norms_remain_gated(self):
        self.assertTrue(self.data['safety_rules']['no_runtime_activation_in_this_lot'])
        self.assertTrue(self.data['safety_rules']['no_facad_norm_runtime_classification'])
        self.assertTrue(self.data['safety_rules']['no_numeric_parity_claim_without_same_trace_export'])

if __name__ == '__main__':
    unittest.main()