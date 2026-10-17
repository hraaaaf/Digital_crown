"""G13 source-anchored identity atlas tests. No patient pixels or model inference."""
import copy
import unittest
from pathlib import Path
from scripts.cephalo_r23g10_annotation_intake import G9_REL,load
from scripts.cephalo_r23g13_public_source_guided_workbook import (
    HOLD_EXPECTED,LEDGER,validate_guide,overlay_html,
)

ROOT=Path(__file__).resolve().parents[2]
def fixture():
    return load(ROOT/LEDGER),load(ROOT/G9_REL)
class SourceGuideTests(unittest.TestCase):
    def rejects(self,guide,matrix=None):
        with self.assertRaises(ValueError):
            validate_guide(guide,matrix or load(ROOT/G9_REL),ROOT)
    def test_twenty_one_actual_source_anchored_names(self):
        g,m=fixture()
        report=validate_guide(g,m,ROOT)
        self.assertEqual(report["source_bound_identifications"],21)
        self.assertFalse(report["clinical_release"])
    def test_six_explicit_operative_definition_holds(self):
        g,m=fixture()
        holds={r["id"] for r in g["rows"] if r["annotation_ui_status"].startswith("HOLD")}
        self.assertEqual(holds,HOLD_EXPECTED)
        self.assertEqual(validate_guide(g,m,ROOT)["human_protocol_holds"],6)
    def test_source_text_not_in_source_fails(self):
        g,m=fixture()
        g["rows"][0]["evidence_excerpt"]="INVENTED PRIMARY SOURCE CLAIM"
        self.rejects(g,m)
    def test_dangerous_traversal_forbidden(self):
        g,m=fixture()
        g["rows"][0]["source_path"]="../secrets.env"
        self.rejects(g,m)
    def test_no_clinical_promotion(self):
        for key in ("clinical_release","operator_anatomy_verified","independent_expert_review"):
            g,m=fixture();g[key]=True;self.rejects(g,m)
        g,m=fixture();g["atlas33_measurements_validated"]=1;self.rejects(g,m)
    def test_no_marking_expert_review_in_source_row(self):
        g,m=fixture()
        g["rows"][1]["expert_consensus_complete"]=True;self.rejects(g,m)
        g,m=fixture()
        g["rows"][1]["clinical_definition_verified"]=True;self.rejects(g,m)
    def test_held_point_cannot_be_silently_promoted(self):
        g,m=fixture()
        g["rows"][0]["annotation_ui_status"]="SOURCE_DESCRIBED__NOT_EXPERT_VERIFIED"
        self.rejects(g,m)
    def test_g9_id_order_and_alias_cannot_drift(self):
        g,m=fixture()
        g["rows"][0]["id"]="Ba_generic";self.rejects(g,m)
        g,m=fixture()
        g["rows"][0]["forbidden_aliases"]=[];self.rejects(g,m)
    def test_corrupted_guide_row_fields_are_rejected(self):
        g,m=fixture()
        g["rows"][1]["image_coords"]={"x":1,"y":2};self.rejects(g,m)
    def test_browser_overlay_preserves_offline_g12_and_source_hold_guard(self):
        g,m=fixture()
        original=(ROOT/"docs/audits/g12_atlas33_public_pixel_workbook.template.html").read_text(encoding="utf8")
        out=overlay_html(original,g)
        self.assertIn('id="source-guide"',out)
        self.assertIn("stopImmediatePropagation()",out)
        self.assertIn("getScreenCTM()",out)
        self.assertIn("clinical_release:false",out)
        self.assertIn("HOLD__EXPERT_PIXEL_RULE_REQUIRED",out)
        self.assertNotIn("/*__G13_GUIDE_DATA__*/",out)
        with self.assertRaises(ValueError):
            overlay_html("<html></html>",g)

if __name__=="__main__": unittest.main()
