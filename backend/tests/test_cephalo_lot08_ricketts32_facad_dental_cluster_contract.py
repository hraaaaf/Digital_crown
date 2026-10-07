import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_ricketts32_facad_dental_cluster_resolution_v1.json"
BACKLOG = ROOT / "docs" / "audits" / "schemas" / "ortho_lot08_facad_dc_unmapped_backlog_v1.json"

class Ricketts32FacadDentalClusterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.backlog = json.loads(BACKLOG.read_text(encoding="utf-8"))

    def test_vendor_occlusal_line_is_not_ricketts_functional_fop(self):
        ol = self.data["facad_constructions"]["OL"]
        self.assertEqual(ol["refs"], ["OLp", "OLa"])
        self.assertEqual(self.data["facad_constructions"]["OLa"]["refs"], ["Is", "Ii"])
        for label in ["Molar rel","Canine rel","Overjet","Overbite","Ii-OL"]:
            self.assertFalse(self.data["resolutions"][label]["dc"]["direct_alias_allowed"])
        self.assertTrue(self.data["safety_rules"]["no_facad_ol_alias_to_ricketts_functional_occlusal_plane"])

    def test_dental_marker_identities_are_source_locked(self):
        m = self.data["marker_identities"]
        self.assertIn("most distal point", m["Mi-d"])
        self.assertIn("most distal point", m["Ms-d"])
        self.assertIn("lower canine tip", m["CNi"])
        self.assertIn("upper canine tip", m["CNs"])

    def test_apog_linear_rows_are_geometry_family_only_until_signed_parity(self):
        low = self.data["resolutions"]["Ii to A-Pog"]
        up = self.data["resolutions"]["Is to A-Pog"]
        self.assertEqual(low["dc"]["geometry_family_measurement_id"], "M_L1_EDGE_APOG_MM_V1")
        self.assertEqual(up["dc"]["geometry_family_measurement_id"], "M_RICKETTS_U1_APOG_PROTRUSION_MM_V1")
        self.assertTrue(low["facad"]["changeRightLeft"])
        self.assertTrue(up["facad"]["changeRightLeft"])
        self.assertFalse(low["dc"]["direct_alias_allowed"])
        self.assertFalse(up["dc"]["direct_alias_allowed"])

    def test_apog_angle_rows_are_geometry_family_only_until_presentation_parity(self):
        low = self.data["resolutions"]["ILi/A-Pog"]
        up = self.data["resolutions"]["ILs/A-Pog"]
        self.assertEqual(low["facad"]["refs"], ["Pog","A","Iia","Ii"])
        self.assertEqual(up["facad"]["refs"], ["Isa","Is","A","Pog"])
        self.assertEqual(low["dc"]["geometry_family_measurement_id"], "M_RICKETTS_L1_APOG_INCLINATION_DEG_V1")
        self.assertEqual(up["dc"]["geometry_family_measurement_id"], "M_RICKETTS_U1_APOG_INCLINATION_DEG_V1")
        self.assertFalse(low["dc"]["direct_alias_allowed"])
        self.assertFalse(up["dc"]["direct_alias_allowed"])

    def test_i_to_ol_preserves_vendor_sign_flags_but_does_not_alias_dc_extrusion(self):
        row = self.data["resolutions"]["Ii-OL"]
        self.assertTrue(row["facad"]["changeSign"])
        self.assertTrue(row["facad"]["changeRightLeft"])
        self.assertEqual(row["dc"]["nearest_measurement_id"], "M_RICKETTS_L1_OCCLUSAL_EXTRUSION_MM_V1")
        self.assertFalse(row["dc"]["direct_alias_allowed"])

    def test_backlog_moves_exactly_this_cluster_out_of_unmapped(self):
        profile = self.backlog["profiles"]["Ricketts (32 F)"]
        resolved = {row["facad_label"] for row in profile["resolved_items"]}
        cluster = set(self.data["scope"])
        self.assertTrue(cluster.issubset(resolved))
        self.assertTrue(cluster.isdisjoint(profile["unmapped"]))
        self.assertEqual(profile["unmapped"], [])
        self.assertEqual(self.backlog["totals"]["unmapped_items"], 0)
        self.assertEqual(
            self.backlog["high_review_progress"]["Ricketts (32 F)"]["resolved_total"], 26
        )
        self.assertEqual(
            self.backlog["high_review_progress"]["Ricketts (32 F)"]["remaining_unmapped"], 0
        )

    def test_runtime_and_norms_remain_gated(self):
        rules = self.data["safety_rules"]
        self.assertTrue(rules["no_runtime_activation_in_this_lot"])
        self.assertTrue(rules["no_facad_norm_runtime_classification"])
        self.assertTrue(rules["no_numeric_or_signed_parity_claim_without_same_trace_export"])

if __name__ == "__main__":
    unittest.main()
