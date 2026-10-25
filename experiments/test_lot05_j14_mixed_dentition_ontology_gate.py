"""LOT05 J14 public CI: 13 fixture-only mixed-dentition ontology tests."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).with_name("lot05_j14_mixed_dentition_ontology_gate.py")
S = importlib.util.spec_from_file_location("lot05_j14_module", P)
assert S and S.loader
M = importlib.util.module_from_spec(S)
S.loader.exec_module(M)


class MixedDentitionSynthetic(unittest.TestCase):
    def test_32_permanent_classes(self):
        self.assertEqual(len(M.PERMANENT_32), 32)
        self.assertEqual(M.classify_fdi("23"), "permanent")

    def test_20_primary_classes(self):
        self.assertEqual(len(M.PRIMARY_20), 20)
        self.assertEqual(M.classify_fdi("53"), "primary")
        self.assertEqual(M.classify_fdi("63"), "primary")

    def test_disjoint_ontologies(self):
        self.assertFalse(M.PRIMARY_20 & M.PERMANENT_32)

    def test_primary_53_confirmed_must_block(self):
        self.assertEqual(M.gate_decision({"fdi":"53","clinical_status":"confirmed"}),
                         "BLOCK_PRIMARY_OUTSIDE_PERMANENT32_ONTOLOGY")

    def test_primary_63_confirmed_must_block(self):
        self.assertEqual(M.gate_decision({"fdi":"63","clinical_status":"confirmed"}),
                         "BLOCK_PRIMARY_OUTSIDE_PERMANENT32_ONTOLOGY")

    def test_primary_63_tentative_must_block(self):
        self.assertEqual(M.gate_decision({"fdi":"63","clinical_status":"tentative"}),
                         "BLOCK_UNCONFIRMED_CLINICAL_DECISION")

    def test_permanent_23_tentative_must_block(self):
        self.assertEqual(M.gate_decision({"fdi":"23","clinical_status":"tentative"}),
                         "BLOCK_UNCONFIRMED_CLINICAL_DECISION")

    def test_permanent_confirmed_still_requires_QA(self):
        self.assertEqual(M.gate_decision({"fdi":"48","clinical_status":"confirmed"}),
                         "ELIGIBLE_FOR_LATER_PRIVATE_GEOMETRY_AND_COLLISION_QA")

    def test_invalid_numeral_or_primary_number(self):
        for fdi in ("93", "68", "40", "00", "5", "５３", " 53", ""):
            with self.subTest(fdi=fdi), self.assertRaises(M.OntologyGateError):
                M.classify_fdi(fdi)

    def test_reject_nonstring_fdi_no_implicit_coercion(self):
        for fdi in (63, 53, None, 63.0):
            with self.subTest(fdi=fdi), self.assertRaises(M.OntologyGateError):
                M.classify_fdi(fdi)

    def test_reject_unknown_or_missing_certainty(self):
        for record in ({"fdi":"63","clinical_status":"maybe"},
                       {"fdi":"63"}, {"fdi":"63","clinical_status":True}):
            with self.subTest(record=record), self.assertRaises(M.OntologyGateError):
                M.gate_decision(record)

    def test_no_case_ids_or_coordinates_in_schema(self):
        with self.assertRaises(M.OntologyGateError):
            M.gate_decision({"fdi":"23","clinical_status":"confirmed",
                             "sample_id":"synthetic", "bbox":[.5,.5,.2,.1]})

    def test_aggregate_safe_and_no_release_claims(self):
        result=M.aggregate_only([
            {"fdi":"23","clinical_status":"confirmed"},
            {"fdi":"53","clinical_status":"confirmed"},
            {"fdi":"63","clinical_status":"tentative"}])
        self.assertEqual(result["decision_count"], 3)
        self.assertEqual(result["confirmed_permanent_candidates_needing_private_QA"], 1)
        self.assertEqual(result["blocked_primary_decisions"], 1)
        self.assertEqual(result["blocked_unconfirmed_decisions"], 1)
        self.assertFalse(result["clinically_validated"])
        self.assertFalse(result["patient_independence_proven"])
        self.assertFalse(result["commercial_rights_cleared"])

if __name__ == "__main__":
    unittest.main()
