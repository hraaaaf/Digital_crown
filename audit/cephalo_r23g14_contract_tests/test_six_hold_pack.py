"""Negative assertions for G14 independent-human HOLD pack, synthetic metadata only."""
import copy
import unittest
from pathlib import Path
from scripts.cephalo_r23g10_annotation_intake import G9_REL,load
from scripts.cephalo_r23g13_public_source_guided_workbook import LEDGER as G13_LEDGER,HOLD_EXPECTED
from scripts.cephalo_r23g14_six_hold_review_workbook import REVIEW_PACK,verify_packet,add_review_cards
ROOT=Path(__file__).resolve().parents[2]
def ctx():
    return load(ROOT/REVIEW_PACK),load(ROOT/G13_LEDGER),load(ROOT/G9_REL)
class G14Tests(unittest.TestCase):
    def reject(self,pack,g13=None,matrix=None):
        _,g0,m0=ctx()
        with self.assertRaises(ValueError):
            verify_packet(pack,g13 or g0,matrix or m0,ROOT)
    def test_six_exact_holds_with_zero_independent_evidence(self):
        p,g,m=ctx();v=verify_packet(p,g,m,ROOT)
        self.assertEqual(v["review_dossiers"],6)
        self.assertEqual(v["source_guides_cross_checked"],21)
        self.assertEqual(v["independent_orthodontist_signatures_verified"],0)
        self.assertFalse(v["clinical_release"])
        self.assertEqual({c["id"] for c in p["cards"]},HOLD_EXPECTED)
    def test_refuse_approval_claims(self):
        for key in ("local_atlas_primary_source_chapter_manually_checked",
                    "independent_reviewer_credentials_verified",
                    "independent_reviewer_a_signed","independent_reviewer_b_signed",
                    "clinical_release","image_calibration_verified","image_orientation_verified"):
            p,g,m=ctx();p[key]=True;self.reject(p,g,m)
    def test_refuse_silent_unlock_and_measurement_promotion(self):
        p,g,m=ctx();p["unlockable_hold_ids"]=["Ba"];self.reject(p,g,m)
        p,g,m=ctx();p["atlas33_clinical_measurements_validated"]=1;self.reject(p,g,m)
        p,g,m=ctx();p["hold_count"]=5;self.reject(p,g,m)
    def test_refuse_fabricated_reviewer_consensus(self):
        for key in ("reviewer_a_independent_source_check",
                    "reviewer_b_independent_source_check",
                    "illustrated_example_source_locked",
                    "ambiguity_and_not_visible_policy_accepted",
                    "interobserver_consensus_verified","clinical_use_authorized"):
            p,g,m=ctx();p["cards"][0][key]=True;self.reject(p,g,m)
    def test_refuse_generic_substitutions(self):
        p,g,m=ctx();p["cards"][0]["id"]="Ba_generic";self.reject(p,g,m)
        p,g,m=ctx();p["cards"][1]["extra_forbidden_aliases"]=[];self.reject(p,g,m)
        p,g,m=ctx();p["cards"][2]["decision"]="RELEASED";self.reject(p,g,m)
    def test_missing_source_passage_is_not_citation(self):
        p,g,m=ctx();p["cards"][0]["source_lock_excerpt"]="Fake Atlas quotation";self.reject(p,g,m)
        p,g,m=ctx();g["rows"][0]["source_path"]="docs/audits/fake.md";self.reject(p,g,m)
    def test_web_sources_cannot_be_untrusted_or_called_atlas(self):
        for url in ("http://pubmed.ncbi.nlm.nih.gov/281884/",
                    "https://evil.example.com/malware",
                    "https://pubmed.ncbi.nlm.nih.gov/281884/?patient=private",
                    "https://example@pubmed.ncbi.nlm.nih.gov/281884/"):
            p,g,m=ctx();p["cards"][1]["external_corroboration_not_atlas_authority"][0]["url"]=url;self.reject(p,g,m)
    def test_each_review_question_must_be_concrete(self):
        p,g,m=ctx();p["cards"][0]["provisional_questionnaire_fr"]=[]
        self.reject(p,g,m)
        p,g,m=ctx();p["cards"][0]["candidate_rule_for_expert_discussion_only_fr"]="Just click"
        self.reject(p,g,m)
    def test_no_patient_or_coordinate_payload_allowed(self):
        p,g,m=ctx();p["cards"][0]["patient_id"]="123";self.reject(p,g,m)
        p,g,m=ctx();p["cards"][0]["x"]=12;self.reject(p,g,m)
    def test_read_only_arbiter_browser_extension(self):
        p,g,m=ctx()
        html="""<html><body><main><aside><section id="source-guide"></section></aside></main></body></html>"""
        out=add_review_cards(html,p)
        self.assertIn('id="g14-arbitration"',out)
        self.assertIn("G14_PACK",out)
        self.assertIn("0/2 validations expertes",out)
        self.assertNotIn("/*__G14_PACKET__*/",out)
        with self.assertRaises(ValueError):add_review_cards("<html></html>",p)
if __name__=="__main__":unittest.main()
