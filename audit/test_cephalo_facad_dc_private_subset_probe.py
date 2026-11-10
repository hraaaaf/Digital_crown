"""Synthetic-only tests of private FACAD bridge; no real FACAD exports in CI."""
from __future__ import annotations
import unittest

from audit import cephalo_facad_dc_private_subset_probe as d


def demo_points():
    # Fictitious landmarks, NOT extracted from Robert.
    return {
        'Ii':(0.,0.), 'Iia':(1.,2.), 'Is':(2.,-1.),'Isa':(1.,-3.),
        'A':(0.,-1.),'Pog':(1.,3.),'Go':(-4.,0.),'Me':(4.,0.),
        'N':(0.,-5.),**{f'SYNTHETIC_{i}':(float(i),float(i+2)) for i in range(22)}
    }


class PrivateDCSubsetProbeTests(unittest.TestCase):
    def test_synthetic_real_dc_functions_return_four_finite_angles(self):
        result = d.raw_helpers(demo_points())
        self.assertEqual(set(result), {'ILi/A-Pog','ILs/A-Pog','InterIncisal','Facial cone angle'})
        self.assertTrue(all(v >= 0 and v <= 180 for v in result.values()))

    def test_never_promotes_synthetic_to_clinical_parity(self):
        p = demo_points()
        values = {k:(0.0, 'mm' if k in ('Convexity','Ii to A-Pog','Is to A-Pog','Li-EL','Upper lip len') else '°') for k in d.FACTOR_32}
        shared = {k:values[k] for k in d.FACTOR_13}
        result = d.comparison(values,shared,p,p.copy())
        self.assertEqual(result['dc_geometry_helpers_executed'],4)
        self.assertEqual(result['clinical_numeric_parities_verified'],0)
        self.assertFalse(result['dc_full_runtime_adapter_executed'])
        self.assertTrue(result['clinical_no_go'])
        self.assertEqual(sum(1 for x in result['rows'] if x['dc_helper'] is None),5)

    def test_refuses_swapped_or_changed_markers(self):
        p = demo_points()
        vals = {k:(0., '°') for k in d.FACTOR_32}
        try:
            d.comparison(vals,{k:vals[k] for k in d.FACTOR_13},p,{**p,'Ii':(9.,9.)})
        except ValueError as exc:
            self.assertIn('markers disagree',str(exc))
        else:
            self.fail('source change not rejected')

    def test_refuses_facad_numeric_drift(self):
        p=demo_points()
        val={k:(0.,'°') for k in d.FACTOR_32}
        val['ILi/A-Pog']=(12.0,'°')
        with self.assertRaisesRegex(ValueError,'shared vendor values disagree'):
            d.comparison(val,{k:(0.,'°') for k in d.FACTOR_13},p,p)

    def test_rejects_wrong_original_factor_roster(self):
        source=("Ricketts (13 F)\nPretreatment tracing (Copie)\n"
                "Valeur\tOriginal\tNorme\tUnité\tDévO\n"
                "Unknown\t1,5\t2±1\t°\t+\n")
        with self.assertRaisesRegex(ValueError,'roster'):
            d.parse_values(source,'13F')

    def test_missing_calibrated_marker_export_fails(self):
        with self.assertRaisesRegex(ValueError,'Object Values'):
            d.parse_points("Pretreatment tracing (Copie)\nBa\t8,7\t95,0")

    def test_cross_coordinate_unit_explicit_mm(self):
        # Source is already metric and not multiplied by 0.038853.
        self.assertTrue('NO_FH_REFERENCE' in d.BLOCKED['Li-EL'])
        self.assertIn('ANS_STS_DIFFERS',d.BLOCKED['Upper lip len'])


if __name__ == '__main__':
    unittest.main()
