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
    # Real format: typed measurement IDs are evidence-node IDs; the M_* IDs
    # only exist in a separate canonical convergence projection.
    cases = [
        ("M_SNA_DEG_V1", "STEINER_SNA_DEG_V1", 82.0),
        ("M_ANB_DEG_V1", "STEINER_ANB_DEG_V1", 4.5),
        ("M_U1_NA_DEG_V1", "STEINER_U1_NA_DEG_V1", 25.0),
        ("M_IMPA_GOME_DEG_V1", "TWEED_IMPA_DEG_V1", None),
    ]
    raws, canonical = [], []
    for i, (canonical_id, method, value) in enumerate(cases):
        ref = f"evidence:typed:{i}"
        status = "AVAILABLE" if value is not None else "NOT_COMPUTABLE"
        raws.append({
            "measurement_id": ref, "method_id": method,
            "availability_status": status, "value": value, "unit": "°",
            "scientific_source": "EVIDENCE_GRAPH_V1",
        })
        canonical.append({
            "canonical_measurement_id": canonical_id,
            "value_authority_method_id": method,
            "measurement_refs": [ref],
            "availability_status": status, "value": value, "unit": "°",
        })
    # Deliberately unknown typed node must never appear.
    raws.append({"measurement_id":"evidence:unmapped:923","method_id":"UNKNOWN",
                 "availability_status":"AVAILABLE","value":150.0,"unit":"°",
                 "scientific_source":"EVIDENCE_GRAPH_V1"})
    return {
        "patient_id": 17, "analysis_id": 41, "analysis_revision": 3,
        "document_state": "INCOMPLETE", "clinical_validation_available": False,
        "active_runtime_chain_verified": True,
        "blocking_gates": ["r14_authoritative_snapshot_not_persisted"],
        "measurements": raws, "canonical_measurements": canonical,
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
        self.assertEqual(len(odf["dentoalveolaire"]), 1)
        self.assertFalse(any("Non calculable" in row["value"] for row in odf["osseuse"] + odf["dentoalveolaire"]))
        self.assertFalse(odf["moulages"])
        self.assertEqual(odf["resume_diagnostique"], "")
        self.assertEqual(odf["plan_traitement"], "")
        self.assertNotIn("Mesure complémentaire", str(odf))
        self.assertNotIn("ANALYSIS_MEASURE_923", str(odf))

    def test_runtime_deg_unit_is_equivalent_to_degree_symbol_only(self):
        # Production typed graph uses 'deg', while the display registry uses '°'.
        # Do not silently drop genuine source-bound angles or accept radians/mm.
        source = typed_study()
        for row in source['measurements']:
            if row.get('unit') == '°': row['unit'] = 'deg'
        for row in source['canonical_measurements']:
            row['unit'] = 'deg'
        odf = build_ortho_bilan_document(source)
        self.assertEqual(odf['osseuse'][0], {'label':'SNA','value':'82 °'})
        self.assertEqual(odf['osseuse'][1], {'label':'ANB','value':'4.5 °'})
        self.assertEqual(odf['dentoalveolaire'][0]['value'], '25 °')
        for invalid in ('rad','mm','°'):
            tampered = deepcopy(source)
            tampered['canonical_measurements'][0]['unit'] = invalid
            self.assertNotIn('SNA', [row['label'] for row in build_ortho_bilan_document(tampered)['osseuse']])

    def test_g3_source_matched_image_never_prints_uncalibrated_mm(self):
        source = typed_study()
        source['lab_image_landmark_alignment'] = 'VERIFIED_AARIZ_EXPERT_PAIR'
        source['measurements'].append({
            'measurement_id':'evidence:typed:metric', 'method_id':'MCNAMARA_CO_A_CANONICAL_MM_V2',
            'availability_status':'AVAILABLE', 'value':42.0, 'unit':'mm',
            'scientific_source':'EVIDENCE_GRAPH_V1',
        })
        source['canonical_measurements'].append({
            'canonical_measurement_id':'M_CO_A_MM_V1',
            'value_authority_method_id':'MCNAMARA_CO_A_CANONICAL_MM_V2',
            'measurement_refs':['evidence:typed:metric'],
            'availability_status':'AVAILABLE', 'value':42.0, 'unit':'mm',
        })
        odf = build_ortho_bilan_document(source)
        self.assertIn('SNA', [row['label'] for row in odf['osseuse']])
        self.assertNotIn('Longueur maxillaire Co-A', [row['label'] for row in odf['osseuse']])

    def test_canonical_is_never_promoted_if_typed_source_disagrees(self):
        source = typed_study()
        for mutation in (
            {"value": 117.0},
            {"unit": "mm"},
            {"measurement_refs": ["nonexistent-evidence-node"]},
            {"value_authority_method_id": "UNKNOWN"},
            {"availability_status": "NOT_COMPUTABLE"},
        ):
            bad = deepcopy(source)
            bad["canonical_measurements"][0].update(mutation)
            names = [r["label"] for r in build_ortho_bilan_document(bad)["osseuse"]]
            self.assertNotIn("SNA", names, mutation)

    def test_no_direct_raw_id_leak_when_canonical_missing(self):
        study = typed_study()
        study["canonical_measurements"] = []
        result = build_ortho_bilan_document(study)
        self.assertFalse(result["osseuse"])
        self.assertFalse(result["dentoalveolaire"])

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
        # Authenticated practitioner NOTE approval is independent of R14:
        # scientific clinical_validation_available must stay False.
        source["practitioner_sections_authorized"] = True
        self.assertFalse(source["clinical_validation_available"])
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

    def test_source_bound_trace_inside_first_phase_has_weasy_reportlab_parity(self):
        # Synthetic colored pixels solely to verify paper layouts.
        # Real Aariz image-to-landmark SHA256 and geometry are checked in G3.
        from PIL import Image
        from base64 import b64encode
        from io import BytesIO
        image = Image.new("RGB", (160, 200), (24, 54, 76))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        encoded = b64encode(buffer.getvalue()).decode("ascii")
        study=typed_study()
        plate={
            "contract_version":"ODF_CEPHALOMETRIC_GEOMETRY_V1",
            "kind":"GEOMETRIC_CEPHALOMETRIC_TRACING",
            "data_uri":"data:image/jpeg;base64," + encoded,
            "image_b64":encoded,
            "caption":"Aariz Cephalometric Dataset (CC BY 4.0), recherche uniquement",
            "source_url":"https://doi.org/10.1038/s41597-025-05542-3",
            "legend":[{"name": x, "color":"#44C5FF"} for x in
                      ("SN","FH","NA","NB","Go–Me","U1","L1")],
        }
        study["lab_verified_research_figure"]=plate
        self.assertIsNone(build_ortho_bilan_document(study)["research_figure"])
        study["lab_image_landmark_alignment"]="VERIFIED_AARIZ_EXPERT_PAIR"
        self.assertEqual(build_ortho_bilan_document(study)["research_figure"],plate)
        with TemporaryDirectory() as root:
            generator=BilanOrthoPDFGenerator(root)
            for backend in ("weasyprint","reportlab"):
                pdf_path=str(Path(root)/(backend+"-annex.pdf"))
                getattr(generator, f"_generate_{backend}")(vm(),pdf_path,projection=study)
                pdf=PdfReader(pdf_path)
                self.assertGreaterEqual(len(pdf.pages),2)
                all_text="\\n".join(p.extract_text() or "" for p in pdf.pages)
                self.assertIn("Tracé céphalométrique",all_text)
                self.assertIn("Aariz Cephalometric Dataset",all_text)
                self.assertLess(all_text.index("Tracé céphalométrique"),
                                all_text.index("A. Analyse osseuse"))
                self.assertLess(all_text.index("Tracé céphalométrique"),
                                all_text.index("Plan de traitement"))
                self.assertNotIn("Non calculable",all_text)

    def test_g5_two_views_precede_measurements_in_both_pdf_engines(self):
        # Synthetic imagery ONLY for pagination/layout. This is NOT an
        # anatomical reference or a clinically approved Aariz tracing.
        from PIL import Image
        from base64 import b64encode
        from io import BytesIO
        source=typed_study()
        radio=Image.new("RGB",(160,200),(33,54,73))
        blank=Image.new("RGB",(160,200),(250,250,250))
        def encoded(image):
            buffer=BytesIO();image.save(buffer,format="JPEG")
            return b64encode(buffer.getvalue()).decode("ascii")
        r,c=encoded(radio),encoded(blank)
        source["lab_image_landmark_alignment"]="VERIFIED_AARIZ_EXPERT_PAIR"
        source["lab_verified_research_figure"]={
            "kind":"G5_MANUAL_ANATOMICAL_TRACE",
            "contract_version":"ODF_ANATOMIC_TRACE_V1",
            "image_b64":r,"data_uri":"data:image/jpeg;base64,"+r,
            "anatomical_only_b64":c,
            "anatomical_only_data_uri":"data:image/jpeg;base64,"+c,
            "caption":"Aariz Cephalometric Dataset (CC BY 4.0) - TEST LAYOUT",
            "source_url":"https://doi.org/10.1038/s41597-025-05542-3",
            "legend":[{"name":x,"color":"#28466A"} for x in ("SN","FH","NA","NB")],
        }
        with TemporaryDirectory() as root:
            gen=BilanOrthoPDFGenerator(root)
            for name in ("weasyprint","reportlab"):
                output=str(Path(root)/(name+"-g5.pdf"))
                getattr(gen,f"_generate_{name}")(vm(),output,projection=source)
                pages=PdfReader(output).pages
                text="\\n".join(p.extract_text() or "" for p in pages)
                self.assertIn("Tracé céphalométrique",text)
                self.assertIn("Tracé anatomique",text)
                self.assertIn("vue épurée",text)
                self.assertLess(text.index("Tracé céphalométrique"),
                                text.index("Tracé anatomique"))
                self.assertLess(text.index("Tracé anatomique"),
                                text.index("Analyse osseuse"))
                self.assertLess(text.index("Analyse osseuse"),
                                text.index("Examen des moulages"))
                self.assertNotIn("Non calculable",text)
                self.assertGreaterEqual(len(pages),2)
                import fitz
                with fitz.open(output) as rendered:
                    self.assertGreaterEqual(sum(len(page.get_images()) for page in rendered),2,
                        'Both clinical overlay and white anatomical drawing must be embedded')

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
                self.assertIn("Inclinaison incisive supérieure",result)
                self.assertNotIn("Non calculable",result)
                self.assertNotIn("Mesure complémentaire",result)
                self.assertNotIn("ANALYSIS_MEASURE",result)
                self.assertNotIn("DOCUMENT CLINIQUE INCOMPLET",result)
                self.assertNotIn("PRÉ-BILAN",result)
                self.assertNotIn("Classe II inventée",result)
        self.assertEqual(source,original)

if __name__=="__main__":
    unittest.main()
