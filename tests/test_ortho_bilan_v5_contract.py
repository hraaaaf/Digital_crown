"""V5 contract tests: real four-phase ODF, no fake values or clinical promotion."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from PyPDF2 import PdfReader

from backend.services.ortho_bilan_document_v5 import (
    build_ortho_bilan_document, MESURES_OSSEUSES, MESURES_DENTOALVEOLAIRES,
)
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator

def typed_study():
    return {
        "patient_id": 17, "analysis_id": 41, "analysis_revision": 3,
        "document_state": "INCOMPLETE", "clinical_validation_available": False,
        "active_runtime_chain_verified": True,
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "measurements": [
            {"measurement_id":"M_SNA_DEG_V1","availability_status":"AVAILABLE",
             "value":82.0,"unit":"°","scientific_source":"EVIDENCE_GRAPH_V1"},
            {"measurement_id":"M_ANB_DEG_V1","availability_status":"AVAILABLE",
             "value":4.5,"unit":"°","scientific_source":"EVIDENCE_GRAPH_V1"},
            {"measurement_id":"M_U1_NA_DEG_V1","availability_status":"AVAILABLE",
             "value":25.0,"unit":"°","scientific_source":"EVIDENCE_GRAPH_V1"},
            {"measurement_id":"M_IMPA_GOME_DEG_V1","availability_status":"NOT_COMPUTABLE",
             "value":None,"unit":"°","scientific_source":"EVIDENCE_GRAPH_V1"},
            {"measurement_id":"ANALYSIS_MEASURE_923","availability_status":"AVAILABLE",
             "value":150.0,"unit":"°","scientific_source":"EVIDENCE_GRAPH_V1"},
        ],
        "stages": [],
    }

def clinician_approved():
    return {
        "contract_version": "ORTHO_PRACTITIONER_APPROVED_V1",
        "validation_state": "APPROVED",
        "patient_id": 17, "analysis_id": 41, "analysis_revision": 3,
        "practitioner_id": 9, "validated_at": "2026-10-23T16:00:00+01:00",
        "moulages": {
            "classe_molaire_droite": "Classe I (cas synthétique)",
            "classe_molaire_gauche": "Classe I (cas synthétique)",
            "ddm_maxillaire": -3.0,
        },
        "resume_diagnostique": "Résumé synthétique confirmé par le dentiste de test.",
        "plan_traitement": "Plan synthétique saisi et approuvé par le dentiste de test.",
    }

def vm():
    return SimpleNamespace(
        patient_nom="TEST", patient_prenom="Patient", patient_age="12",
        date_generation="23/10/2026", doctor_name="Dr Salma Atlas - DEMO",
        patient_id=17, cabinet_config={
            "header_lines_fr": ["Dr Salma Atlas - DEMO", "Orthodontie"],
            "header_lines_ar": [],
            "footer_address": "24 avenue fictive, Rabat",
            "margin_top": 3.6, "margin_bottom": 3.2,
            "selected_template": "swiss",
        },
        is_pre_bilan=True, validation_warnings=[],
    )

class OrthoV5DocumentContract(unittest.TestCase):
    def test_canonical_mapping_is_exact_and_registry_grounded(self):
        from backend.services.cephalo_measure_registry import CANONICAL_MEASUREMENTS
        for key in [*MESURES_OSSEUSES, *MESURES_DENTOALVEOLAIRES]:
            self.assertIn(key, CANONICAL_MEASUREMENTS, key)
            self.assertIsNotNone(CANONICAL_MEASUREMENTS[key].unit, key)

    def test_four_phase_fail_closed_preview(self):
        source = typed_study()
        baseline = deepcopy(source)
        odf = build_ortho_bilan_document(source)
        self.assertEqual(source, baseline)
        self.assertEqual([r["label"] for r in odf["osseuse"]], ["SNA", "ANB"])
        self.assertEqual(len(odf["dentoalveolaire"]), 2)
        self.assertEqual(odf["dentoalveolaire"][1]["value"], "Non calculable")
        self.assertFalse(odf["moulages"])
        self.assertEqual(odf["resume_diagnostique"], "")
        self.assertEqual(odf["plan_traitement"], "")
        self.assertNotIn("Mesure complémentaire", str(odf))
        self.assertNotIn("ANALYSIS_MEASURE_923", str(odf))

    def test_no_unverified_values_and_no_legacy_diagnosis_promotion(self):
        source = typed_study()
        source["active_runtime_chain_verified"] = False
        source["ai_diagnostic"] = {"synthese_diagnostique":"Classe II inventée"}
        source["clinical_data"] = {"plan_traitement":"Extraction automatique"}
        odf = build_ortho_bilan_document(source)
        self.assertFalse(odf["osseuse"])
        self.assertFalse(odf["dentoalveolaire"])
        self.assertEqual(odf["resume_diagnostique"], "")
        self.assertEqual(odf["plan_traitement"], "")

    def test_signed_snapshot_requires_full_identity_and_server_clinical_gate(self):
        source = typed_study()
        source["practitioner_approved_sections"] = clinician_approved()
        self.assertFalse(build_ortho_bilan_document(source)["moulages"])
        source["clinical_validation_available"] = True
        source["document_state"] = "COMPLETE"
        source["blocking_gates"] = []
        odf = build_ortho_bilan_document(source)
        self.assertEqual(len(odf["moulages"]), 3)
        self.assertIn("-3 mm", str(odf["moulages"]))
        self.assertIn("confirmé", odf["resume_diagnostique"])
        self.assertIn("approuvé", odf["plan_traitement"])
        for change in [
            {"patient_id": 999}, {"analysis_id": 999},
            {"analysis_revision": 99}, {"validation_state":"DRAFT"},
            {"practitioner_id": 0}, {"validated_at":""},
        ]:
            trial=deepcopy(source)
            trial["practitioner_approved_sections"].update(change)
            bad=build_ortho_bilan_document(trial)
            self.assertFalse(bad["moulages"],change)
            self.assertFalse(bad["resume_diagnostique"],change)
            self.assertFalse(bad["plan_traitement"],change)

    def test_real_pdf_weasyprint_and_fallback_have_same_four_phases(self):
        source = typed_study()
        original=deepcopy(source)
        with TemporaryDirectory() as root:
            generator=BilanOrthoPDFGenerator(root)
            for kind in ("weasyprint","reportlab"):
                path=str(Path(root) / f"{kind}.pdf")
                method=getattr(generator,f"_generate_{kind}")
                method(vm(),path,projection=source)
                result="\n".join(p.extract_text() or "" for p in PdfReader(path).pages)
                headings=[
                    "Analyse céphalométrique", "Analyse osseuse",
                    "Analyse dento-alvéolaire", "Examen des moulages",
                    "Résumé diagnostique", "Plan de traitement",
                ]
                offsets=[result.index(h) for h in headings]
                self.assertEqual(offsets,sorted(offsets))
                self.assertIn("SNA",result)
                self.assertIn("IMPA",result)
                self.assertIn("Non calculable",result)
                self.assertNotIn("Mesure complémentaire",result)
                self.assertNotIn("ANALYSIS_MEASURE",result)
                self.assertNotIn("DOCUMENT CLINIQUE INCOMPLET",result)
                self.assertNotIn("PRÉ-BILAN",result)
                self.assertNotIn("Classe II inventée",result)
        self.assertEqual(source,original)

if __name__=="__main__":
    unittest.main()
