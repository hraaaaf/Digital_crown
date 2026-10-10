"""D3E.20 source-only review integrity, two adversarial test lenses."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
GATE=ROOT/"scripts/facad_314_d3e20_review_decision_gate.py"
DECISION=ROOT/"docs/audits/FACAD_314_D3E20_DUAL_REVIEW_DECISION.json"
spec=importlib.util.spec_from_file_location("d3e20_gate",GATE)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

# Independent oracle (not derived from the mutable gate).
EXPECTED_IDS={"SEC-01","SEC-02","SEC-03","SEC-04","SEC-05",
              "SCI-01","SCI-02","SCI-03","SCI-04","SCI-05"}
EXPECTED_BLOCKERS={"SEC-01","SEC-02","SEC-03","SCI-01","SCI-02","SCI-03"}
EXPECTED_FALSE_KEYS=set(["external_privacy_reviewer_verified","external_scientific_reviewer_verified","same_exact_head_external_reviews_verified","privacy_blockers_cleared","science_blockers_cleared","official_demo_and_license_verified","host_guest_channel_confinement_verified","approved_egress_protocol_verified","source_scoped_attribution_verified","event_completeness_verified","native_experiment_separately_authorized","native_vm_or_iso_operated","facad_or_ilexis_executed","raw_etw_captured_or_exported","clinical_edit_allowed","shared_app_storage_isolation_verified","converged","merge_or_deploy_authorized"])
class A_PrivacyAndReviewTruth(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads(DECISION.read_text(encoding="utf-8"))

    def bad(self):
        with self.assertRaises(gate.ReviewBlocked):
            gate.evaluate(self.plan)

    def test_valid_record_still_no_go(self):
        o=gate.evaluate(self.plan)
        self.assertEqual(o["blockers_open"],6)
        self.assertEqual(o["issues_open"],10)
        self.assertEqual(o["actual_independent_reviewers"],0)
        self.assertFalse(o["native_execution"])

    def test_frozen_oracle_independent_of_gate(self):
        self.assertEqual(set(gate.FINDING_ORACLE),EXPECTED_IDS)
        self.assertEqual({k for k,v in gate.FINDING_ORACLE.items()
                          if v["severity"]=="BLOCKER"},EXPECTED_BLOCKERS)
        self.assertEqual(gate.UNPROVEN,EXPECTED_FALSE_KEYS)

    def test_false_independent_reviewer_fails(self):
        self.plan["external_privacy_reviewer_verified"]=True
        self.bad()

    def test_false_native_clearance_fails(self):
        self.plan["native_experiment_separately_authorized"]=True
        self.bad()

    def test_false_clinical_clearance_fails(self):
        self.plan["clinical_edit_allowed"]=True
        self.bad()

    def test_downgraded_severity_fails(self):
        self.plan["findings"][0]["severity"]="MAJOR"
        self.bad()

    def test_claim_issue_fixed_fails(self):
        self.plan["findings"][0]["status"]="CLOSED"
        self.bad()

    def test_missing_issue_fails(self):
        self.plan["findings"].pop()
        self.bad()

    def test_duplicate_finding_fails(self):
        self.plan["findings"][1]=self.plan["findings"][0].copy()
        self.bad()

    def test_unknown_extra_finding_field_fails(self):
        self.plan["findings"][0]["patient_path"]="private"
        self.bad()

    def test_wrong_reviewed_sha_fails(self):
        self.plan["review_target_sha"]="0"*40
        self.bad()

    def test_wrong_review_status_fails(self):
        self.plan["reviewer_claim"]="INDEPENDENT_REVIEWED"
        self.bad()

    def test_wrong_decision_fails(self):
        self.plan["decision"]="GO_NATIVE"
        self.bad()

    def test_extra_top_level_claim_fails(self):
        self.plan["no_exfiltration_proven"]=True
        self.bad()

    def test_nullable_false_fails(self):
        self.plan["converged"]=None
        self.bad()

    def test_numeric_score_forgery_fails(self):
        self.plan["security_native_proof_score_10"]=1
        self.bad()

class B_EvidenceAndParserTruth(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads(DECISION.read_text(encoding="utf-8"))

    def test_type_bool_vs_zero(self):
        self.plan["raw_etw_captured_or_exported"]=0
        with self.assertRaises(gate.ReviewBlocked):gate.evaluate(self.plan)

    def test_fake_scientific_reviewer(self):
        self.plan["external_scientific_reviewer_verified"]=True
        with self.assertRaises(gate.ReviewBlocked):gate.evaluate(self.plan)

    def test_fake_writer_proof(self):
        self.plan["source_scoped_attribution_verified"]=True
        with self.assertRaises(gate.ReviewBlocked):gate.evaluate(self.plan)

    def test_fake_event_proof(self):
        self.plan["event_completeness_verified"]=True
        with self.assertRaises(gate.ReviewBlocked):gate.evaluate(self.plan)

    def test_parser_rejects_duplicate_key(self):
        with self.assertRaises(gate.ReviewBlocked):
            gate.unique_pairs([("decision","NO_GO"),("decision","GO_NATIVE")])

    def test_cli_valid_record_reports_no_go(self):
        p=subprocess.run([sys.executable,str(GATE),"--decision",str(DECISION)],
                         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        for x in ["D3E20_BLOCKERS_OPEN=6","D3E20_MAJOR_OPEN=4",
                  "D3E20_EXTERNAL_INDEPENDENT_REVIEWERS=0",
                  "CLINICAL_EDIT_ALLOWED=false","CONVERGED=false"]:
            self.assertIn(x,p.stdout)

    def test_cli_missing_file_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            p=subprocess.run([sys.executable,str(GATE),"--decision",str(Path(td)/"gone")],
                             capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertNotIn("Traceback",p.stderr)

    def test_cli_rejects_duplicate_json(self):
        with tempfile.TemporaryDirectory() as td:
            pth=Path(td)/"bad.json"
            pth.write_text('{"decision":"GO","decision":"NO_GO"}',encoding="utf-8")
            p=subprocess.run([sys.executable,str(GATE),"--decision",str(pth)],
                             capture_output=True,text=True)
            self.assertEqual(p.returncode,2)

    def test_cli_rejects_bom(self):
        with tempfile.TemporaryDirectory() as td:
            pth=Path(td)/"bom.json"
            pth.write_bytes(bytes([239,187,191])+DECISION.read_bytes())
            with self.assertRaisesRegex(gate.ReviewBlocked,"INVALID_ENCODING"):
                gate.load(pth)

    def test_cli_rejects_nul(self):
        with tempfile.TemporaryDirectory() as td:
            pth=Path(td)/"nul.json"
            pth.write_bytes(DECISION.read_bytes()+bytes([0]))
            with self.assertRaisesRegex(gate.ReviewBlocked,"INVALID_ENCODING"):
                gate.load(pth)

    def test_non_dict_fails(self):
        with self.assertRaises(gate.ReviewBlocked):
            gate.evaluate([])

    def test_swap_finding_domain_fails(self):
        self.plan["findings"][0]["domain"]="SCIENCE"
        with self.assertRaises(gate.ReviewBlocked):gate.evaluate(self.plan)

if __name__=="__main__":
    unittest.main()
