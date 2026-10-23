"""Premium V3 — real synthetic PDF parity without a patient or clinical promotion."""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from PyPDF2 import PdfReader

from backend.services.cephalo_pdf_presentation import clinical_term, measurement_value
from backend.services.document_branding_contract import serialize_document_branding
from backend.services.generators.bilan_ortho_gen import BilanOrthoPDFGenerator

TEMPLATES = ("swiss", "royal", "clinical", "modern", "heritage")

def synthetic_branding(template="swiss"):
    return {
        "selected_template": template,
        "selected_theme": "rose",  # deliberate counterexample: never drives PDF identity
        "nom_praticien": "Dr Test Cabinet",
        "nom_cabinet": "Cabinet Synthétique",
        "header_customized": True,
        "header_lines_fr": ["Dr Test Cabinet", "Cabinet Synthétique"],
        "header_lines_ar": [],
        "footer_address": "Rue Exemple 123",
        "footer_phones": "06 00 00 00 00",
        "contacts_json": {},
        "primary_color": "#29476a", "secondary_color": "#506379",
        "accent_color": "#a9b2c2", "font_fr": "outfit",
        "margin_top": 3.6, "margin_bottom": 3.2,
        "qr_code_enabled": False, "use_letterhead": False,
        "hide_header": False, "hide_footer": False,
    }

def synthetic_projection(n=95):
    measurement = []
    for i in range(n):
        available = i % 3 == 0
        measurement.append({
            "measurement_id": ("SNA" if i == 0 else f"ANALYSIS_MEASURE_{i:03d}"),
            "availability_status": "AVAILABLE" if available else "NOT_COMPUTABLE",
            "value": 82.0 if available else None,
            "unit": "deg", "method_id": "STEINER_SNA_DEG_V1",
            "method_version": "1", "scientific_source": "EVIDENCE_GRAPH_V1",
            "calibration_ref": "non requise",
        })
    return {
        "analysis_id": 41, "analysis_revision": 3,
        "contract_version": "CEPHALO_PDF_PROJECTION_V1",
        "document_state": "INCOMPLETE",
        "authority": "BACKEND_TYPED_EVIDENCE_AND_R15_STUDIO",
        "active_runtime_chain_verified": False,
        "clinical_validation_reason": "R14 NO VERIFIED PRACTITIONER SNAPSHOT",
        "blocking_gates": ["diagnostic_rule_registry_empty",
                           "r14_authoritative_snapshot_not_persisted"],
        "measurements": measurement,
        "stages": [
            {"stage_id": "R11", "title": "Diagnostic scientifique",
             "presentation_state": "BLOCKED",
             "blocking_gates": ["diagnostic_rule_registry_empty"],
             "missing_data_refs": ["r11_provenance_missing"]},
        ],
    }

def synthetic_vm(template="swiss"):
    return SimpleNamespace(
        patient_nom="TEST", patient_prenom="Synthétique", patient_age="12",
        date_generation="23/10/2026", doctor_name="Dr Test Cabinet",
        cabinet_config=synthetic_branding(template),
        is_pre_bilan=True, validation_warnings=[],
    )

class PdfV3Contract(unittest.TestCase):
    def test_allowlist_separates_theme_and_sensitive_fields(self):
        cabinet = SimpleNamespace(**dict(synthetic_branding(), hashed_password="NEVER_PRINT"))
        branded = serialize_document_branding(cabinet)
        self.assertEqual(branded["selected_template"], "swiss")
        self.assertNotIn("selected_theme", branded)
        self.assertNotIn("hashed_password", branded)
        self.assertEqual(branded["footer_address"], "Rue Exemple 123")

    def test_fail_closed_display_language(self):
        self.assertEqual(clinical_term("NOT_COMPUTABLE"),
                         "Non calculable avec les données disponibles")
        self.assertEqual(measurement_value("82 deg", "BLOCKED"), "Non calculable")
        self.assertNotIn("R14", clinical_term("R14 NO VERIFIED PRACTITIONER SNAPSHOT"))
        self.assertNotIn("method_id", clinical_term("method_id_unknown"))
        self.assertNotIn("source-lock", clinical_term("source-lock SATISFIED"))

    def test_real_weasyprint_a4_all_five_cabinet_templates(self):
        from reportlab.lib.pagesizes import A4
        with tempfile.TemporaryDirectory() as tmp:
            generator = BilanOrthoPDFGenerator(tmp)
            for template in TEMPLATES:
                with self.subTest(template=template):
                    vm = synthetic_vm(template)
                    output = str(Path(tmp) / f"bilan_{template}.pdf")
                    generator._generate_weasyprint(vm, output,
                        projection=synthetic_projection(), user=None)
                    pdf = PdfReader(output)
                    self.assertGreaterEqual(len(pdf.pages), 2)
                    full = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    self.assertIn("Non calculable", full)
                    self.assertNotIn("NOT_COMPUTABLE", full)
                    self.assertNotIn("source-lock", full)
                    self.assertNotIn("EVIDENCE_GRAPH_V1", full)
                    self.assertNotIn("diagnostic_rule_registry_empty", full)
                    self.assertNotIn("Chaîne clinique R11", full)
                    for page in pdf.pages:
                        self.assertAlmostEqual(float(page.mediabox.width), A4[0], delta=0.5)
                        self.assertAlmostEqual(float(page.mediabox.height), A4[1], delta=0.5)
                        body = page.extract_text() or ""
                        self.assertIn("Rue Exemple 123", body,
                                      "Le pied de page BaseTemplate doit apparaître sur chaque page")

    def test_reportlab_fallback_uses_the_same_branding(self):
        with tempfile.TemporaryDirectory() as tmp:
            generator = BilanOrthoPDFGenerator(tmp)
            output = str(Path(tmp) / "reportlab.pdf")
            generator._generate_reportlab(synthetic_vm("heritage"), output,
                                          projection=synthetic_projection(n=25))
            pdf = PdfReader(output)
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            self.assertIn("Rue Exemple 123", text)
            self.assertNotIn("source-lock", text)
            self.assertNotIn("NOT_COMPUTABLE", text)

if __name__ == "__main__":
    unittest.main()
