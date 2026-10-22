"""LOT05/J10H: research-only writing quality and actual PDF rendering contract.

All names, ages, and medical remarks here are deliberately synthetic.
The production route and clinical DB are never called.
"""
from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "backend/services/panoramic_pdf_outline.py"
TEMPLATE = REPO / "backend/templates/panoramic_elite.html"
GENERATOR = REPO / "backend/services/generators/panoramic_elite_gen.py"

spec = importlib.util.spec_from_file_location("j10h_research_outline", SOURCE)
assert spec is not None and spec.loader is not None
outline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(outline)


def sample_md() -> str:
    """Fictitious text; tests report fidelity, not medical plausibility."""
    return """### QUESTION CLINIQUE
- Bilan radiographique demandé pour une question dentaire fictive.

### TECHNIQUE
- Radiographie panoramique numérique.
- Qualité évaluée par le praticien : limitée à cause de la position.

### DENTITION ET ANOMALIES DENTAIRES
- Dent 38 absente, observation déclarée par le praticien.
Description libre complémentaire concernant les dents 11 et 12.

### RÉGIONS PÉRIAPICALES / ENDODONTIE
- Image radioclaire périapicale en regard de la dent 36, décrite par le praticien.

### SINUS MAXILLAIRES
- Domaine non évalué dans ce bilan.

### RÉPONSE À LA QUESTION CLINIQUE
Cette réponse clinique est entièrement rédigée et vérifiée par le praticien.

### SYNTHÈSE
- Les observations documentées concernent les dents 36 et 38.
La corrélation clinique a été indiquée manuellement ; aucune recommandation n'est inférée.
"""


def render(s, *, patient="SYNTHÉTIQUE", doctor="Dr DÉMONSTRATION"):
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from weasyprint import HTML
    from pypdf import PdfReader

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE.parent)),
        autoescape=select_autoescape(enabled_extensions=("html", "xml"), default=True),
    )
    data = {
        "patient_nom": patient,
        "patient_prenom": "EXEMPLE",
        "patient_id": "DEMO-001",
        "patient_age": "35",
        "doctor_name": doctor,
        "date_analyse": "22/10/2026",
        "primary_color": "#16365a",
        "secondary_color": "#64748b",
        "denture_type": "Non documenté",
        "categories": outline.parse_panoramic_report(s),
    }
    html = env.get_template(TEMPLATE.name).render(**data)
    pdf = HTML(string=html, base_url=str(TEMPLATE.parent)).write_pdf()
    reader = PdfReader(io.BytesIO(pdf))
    text = "\n".join((p.extract_text() or "") for p in reader.pages)
    return html, pdf, reader, text


class PanoramicWrittenReportQuality(unittest.TestCase):
    def test_parser_preserves_question_technique_all_findings_and_clinician_prose(self):
        data = outline.parse_panoramic_report(sample_md())
        self.assertEqual(
            [d["kind"] for d in data],
            ["indication", "technique", "observation", "observation",
             "observation", "response", "conclusion"],
        )
        self.assertEqual(data[2]["findings"][-1],
                         "Description libre complémentaire concernant les dents 11 et 12.")
        self.assertEqual(data[5]["findings"][0],
                         "Cette réponse clinique est entièrement rédigée et vérifiée par le praticien.")
        self.assertEqual(data[6]["findings"][-1],
                         "La corrélation clinique a été indiquée manuellement ; aucune recommandation n'est inférée.")
        self.assertNotIn("Aucun foyer infectieux", str(data))
        self.assertNotIn("normal", str(data).lower())

    def test_free_text_without_headers_is_never_dropped(self):
        raw = "Compte rendu rédigé librement.\nAutre observation dentaire FDI 24.\n"
        data = outline.parse_panoramic_report(raw)
        self.assertEqual(data[0]["findings"], [
            "Compte rendu rédigé librement.",
            "Autre observation dentaire FDI 24.",
        ])

    def test_empty_or_heading_only_report_does_not_claim_normality(self):
        for raw in ("", None, "### TECHNIQUE\n\n### CONCLUSION"):
            with self.subTest(raw=raw):
                data = outline.parse_panoramic_report(raw)
                self.assertEqual(len(data), 1)
                self.assertIn("Aucune observation documentée", data[0]["findings"][0])
                self.assertNotIn("normal", str(data).lower())

    def test_real_pdf_retains_written_data_and_is_image_free(self):
        html, pdf, reader, text = render(sample_md())
        self.assertGreaterEqual(len(reader.pages), 1)
        for token in (
            "SYNTHÉTIQUE", "Dr DÉMONSTRATION",
            "COMPTE RENDU", "QUESTION CLINIQUE", "TECHNIQUE",
            "RÉGIONS PÉRIAPICALES", "SYNTHÈSE",
            "Dent 38 absente", "dent 36",
            "Description libre complémentaire",
            "La corrélation clinique a été indiquée manuellement",
            "Observations radiographiques documentées",
        ):
            with self.subTest(token=token):
                self.assertIn(token.lower(), text.lower())
        for idx, page in enumerate(reader.pages):
            self.assertFalse(page.images, f"Page {idx+1}: PDF contains an image")
        self.assertNotIn(b"/Subtype /Image", pdf)
        self.assertNotIn("<img", html.lower())

    def test_long_report_multiple_pages_complete_with_no_radiograph(self):
        raw = "### TECHNIQUE\n- Radiographie panoramique numérique.\n"
        raw += "### DENTITION ET ANOMALIES DENTAIRES\n"
        raw += "".join(
            f"- Observation SYNTHETIQUE-LONG-{i:03d} : constatation du praticien pour test de mise en page.\n"
            for i in range(110)
        )
        raw += "### CONCLUSION\n- FIN-DU-RAPPORT-SYNTHETIQUE.\n"
        html, pdf, reader, text = render(raw)
        self.assertGreaterEqual(len(reader.pages), 3)
        for needle in ("SYNTHETIQUE-LONG-000", "SYNTHETIQUE-LONG-055",
                       "SYNTHETIQUE-LONG-109", "FIN-DU-RAPPORT-SYNTHETIQUE"):
            self.assertIn(needle, text)
        self.assertFalse(any(page.images for page in reader.pages))
        self.assertNotIn("<img", html.lower())

    def test_html_and_svg_injected_as_practitioner_text_not_interpreted(self):
        malicious = (
            "### CONCLUSION\n"
            "- Observation: <img src='file:///medical-secret.png'>\n"
            "- <svg onload='alert(1)'></svg>\n"
            "- <script>alert('x')</script>\n"
            "- Texte **gras** avec FDI 46.\n"
        )
        html, pdf, reader, text = render(
            malicious, patient="<script>patient</script>",
            doctor="Dr <img src='file:///secret.png'>",
        )
        self.assertNotIn("<img", html.lower())
        self.assertNotIn("<script>", html.lower())
        self.assertNotIn("<svg", html.lower())
        self.assertIn("&lt;img", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("FDI 46", text)
        self.assertFalse(any(page.images for page in reader.pages))
        self.assertNotIn(b"/Subtype /Image", pdf)

    def test_elite_generator_has_autoescape_in_the_actual_pdf_path(self):
        s = GENERATOR.read_text(encoding="utf-8")
        self.assertIn("autoescape=select_autoescape", s)
        self.assertIn("parse_panoramic_report(markdown)", s)
        self.assertIn("assert_patient_access", s)
        self.assertNotIn("models.CephaloAnalysis", s)
        self.assertNotIn("pano_url", s)


if __name__ == "__main__":
    unittest.main()
