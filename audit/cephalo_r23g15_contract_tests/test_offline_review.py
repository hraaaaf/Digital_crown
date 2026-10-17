"""Synthetic reviewer submissions only — no human decisions, credentials or PHI."""
import copy
import tempfile
import unittest
from pathlib import Path
from scripts.cephalo_r23g15_offline_independent_review import (
    baseline,blank,check_review,compare,html_form,prepare,G14_SOURCE_HEAD,END_STATUS,
)
ROOT=Path(__file__).resolve().parents[2]
def fake(role,packet,token=None,status="RULE_PROPOSED_FOR_ADJUDICATION"):
    o=blank(role,packet)
    o["reviewer_token"]=token or "synthetic_"+role
    for x in o["cases"]:
        x["status"]=status
        x["atlas_ch13_page_or_figure"]="Atlas2009 chapter13 figure TEST_NOT_REAL"
        x["proposed_pixel_rule"]="SYNTHETIC RULE FOR TEST ONLY: mark a non-anatomic test pixel; never use clinically"
        x["ambiguity_and_not_visible_policy"]="SYNTHETIC policy: do not mark if location ambiguous; NOT_COMPUTABLE"
        x["answers_to_three_questions"]=[
           "SYNTHETIC reply to question one, no real source.", 
           "SYNTHETIC reply to question two, no human review.",
           "SYNTHETIC reply to question three, unresolved evidence."
        ]
    return o

class G15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack=baseline(ROOT)

    def reject(self,a,b):
        with self.assertRaises(ValueError):compare(a,b,self.pack)

    def test_unfilled_form_can_never_be_treated_as_completed(self):
        a,b=blank("A",self.pack),blank("B",self.pack)
        self.reject(a,b)

    def test_individual_roles_and_six_exact_holds(self):
        a=fake("A",self.pack)
        status=check_review(a,"A",self.pack)
        self.assertEqual(len(status),6)
        self.assertEqual([c["id"] for c in a["cases"]],[c["id"] for c in self.pack["cards"]])

    def test_matching_two_synthetic_sessions_never_become_go(self):
        v=compare(fake("A",self.pack),fake("B",self.pack),self.pack)
        self.assertEqual(v["status_agreement_count"],6)
        self.assertEqual(v["status_disagreement_count"],0)
        self.assertEqual(v["status"],END_STATUS)
        self.assertEqual(v["clinically_unlocked_hold_count"],0)
        self.assertEqual(v["actual_signatures_verified"],0)
        self.assertFalse(v["clinical_release"])
        self.assertNotIn("synthetic_A",str(v))
        self.assertNotIn("SYNTHETIC reply",str(v))

    def test_disagreement_is_reported_without_promotion(self):
        a,b=fake("A",self.pack),fake("B",self.pack)
        b["cases"][1]["status"]="HOLD_UNRESOLVED"
        v=compare(a,b,self.pack)
        self.assertEqual(v["status_disagreement_count"],1)
        self.assertEqual(v["status_agreement_count"],5)
        self.assertFalse(v["cases"][1]["clinical_rule_approved"])

    def test_same_reviewer_pseudonym_for_both_is_rejected(self):
        self.reject(fake("A",self.pack,token="same"),fake("B",self.pack,token="same"))

    def test_roles_cannot_be_relabelled(self):
        a,b=fake("A",self.pack),fake("B",self.pack)
        b["role"]="A";self.reject(a,b)
        a,b=fake("A",self.pack),fake("B",self.pack)
        a["g14_parent_head_sha"]="bad";self.reject(a,b)

    def test_cannot_forge_signature_credentials_or_go(self):
        for key in ("human_credentials_externally_verified",
                    "actual_signature_externally_verified","clinical_release"):
            a,b=fake("A",self.pack),fake("B",self.pack)
            a[key]=True
            self.reject(a,b)

    def test_cannot_inject_photos_coordinates_or_patient_record(self):
        for key in ("patient_name","image","landmarks"):
            a,b=fake("A",self.pack),fake("B",self.pack)
            a["cases"][0][key]="something"
            self.reject(a,b)
        a,b=fake("A",self.pack),fake("B",self.pack)
        a["patient_id"]="patient-123"
        self.reject(a,b)

    def test_six_ids_cannot_be_replaced_or_skipped(self):
        a,b=fake("A",self.pack),fake("B",self.pack)
        a["cases"][0]["id"]="Ba_generic";self.reject(a,b)
        a,b=fake("A",self.pack),fake("B",self.pack)
        a["cases"].pop();self.reject(a,b)

    def test_three_human_questions_are_mandatory(self):
        for value in ([None],[],["too short"]*3):
            a,b=fake("A",self.pack),fake("B",self.pack)
            a["cases"][0]["answers_to_three_questions"]=value
            self.reject(a,b)

    def test_rule_proposal_cannot_lack_primary_source_or_pixel_rule(self):
        a,b=fake("A",self.pack),fake("B",self.pack)
        a["cases"][2]["atlas_ch13_page_or_figure"]=""
        self.reject(a,b)
        a,b=fake("A",self.pack),fake("B",self.pack)
        a["cases"][2]["proposed_pixel_rule"]="weak"
        self.reject(a,b)

    def test_protected_folder_gates_and_two_local_html_forms(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"a-b-forms"
            result=prepare(ROOT,dest,self.pack)
            self.assertEqual(result["real_reviews_collected"],0)
            a=(dest/"A"/"independent_review.html").read_text()
            b=(dest/"B"/"independent_review.html").read_text()
            self.assertIn("Relecture indépendante A",a)
            self.assertIn("Relecture indépendante B",b)
            self.assertNotIn("DATA_PLACEHOLDER",a)
            self.assertNotIn("ROLE_PLACEHOLDER",b)
            self.assertNotIn("synthetic_A",a)
            self.assertIn("connect-src 'none'",a)
            with self.assertRaises(ValueError):
                prepare(ROOT,dest,self.pack)

    def test_private_export_never_inside_repo(self):
        with self.assertRaises(ValueError):
            prepare(ROOT,ROOT/"tmp-private-review-test",self.pack)

if __name__=="__main__":unittest.main()
