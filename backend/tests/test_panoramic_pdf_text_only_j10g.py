"""LOT05 / J10G — actual panoramic PDF = written report ONLY.

No patient data, no medical image, no network and no clinical inference.
These tests use artificial metadata / observations only.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "backend/templates/panoramic_elite.html"
ELITE_PY = REPO / "backend/services/generators/panoramic_elite_gen.py"
LEGACY_PY = REPO / "backend/services/generators/panoramic_gen.py"
IA_PY = REPO / "backend/routers/ia.py"


class PanoramicReportTextOnly(unittest.TestCase):
    def test_template_has_no_radiograph_or_any_embedded_image(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        for disallowed in (
            "<img", "pano_url", "cephalo_url", "qr_code_base64",
            "imaging-grid", "main-radio", "secondary-imaging",
            "cephalo-annex", "Synthèse Céphalométrique",
            "Téléradiographie", "Orthopantomogramme (radiographie",
        ):
            with self.subTest(token=disallowed):
                self.assertNotIn(disallowed.lower(), html.lower())
        self.assertIn("Observations radiographiques documentées", html)
        self.assertIn("{{ patient_nom.upper() }}", html)
        self.assertIn("{{ doctor_name }}", html)

    def test_legacy_generator_does_not_open_radiograph_or_embed_it(self):
        import ast
        tree = ast.parse(LEGACY_PY.read_text(encoding="utf-8"))
        methods = [node for cls in tree.body if isinstance(cls, ast.ClassDef)
                   for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "generate_pdf"]
        self.assertEqual(len(methods), 1)
        code = ast.get_source_segment(LEGACY_PY.read_text(encoding="utf-8"), methods[0])
        assert code is not None
        self.assertNotIn("ImageReader(", code)
        self.assertNotIn("img_flowable", code)
        self.assertNotIn("Image(", code)
        self.assertNotIn("CLICHÉ RADIOGRAPHIQUE ANALYSÉ", code)
        # API signature remains backwards compatible.
        self.assertIn("img_rel_path", code.splitlines()[0])

    def test_main_generator_no_longer_reads_radios_or_cephalo_or_qr(self):
        source = ELITE_PY.read_text(encoding="utf-8")
        import ast
        tree = ast.parse(source)
        methods = [node for cls in tree.body if isinstance(cls, ast.ClassDef)
                   for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "generate"]
        self.assertEqual(len(methods), 1)
        code = ast.get_source_segment(source, methods[0])
        assert code is not None
        for token in ("_format_image_url", "CephaloAnalysis", "image_original_path",
                      "qr_service", "generate_document_qr_base64", "_prepare_metrics",
                      "analysis.image_path", "pano_url", "cephalo_url"):
            with self.subTest(token=token):
                self.assertNotIn(token, code)
        self.assertIn('self._categorize_findings(analysis.report_narrative or "")', code)

    def test_protected_pdf_endpoint_uses_only_report_generator(self):
        source = IA_PY.read_text(encoding="utf-8")
        entry = source.index('@router.get("/panoramic/{analysis_id}/pdf")')
        end = source.index("@router.", entry+1)
        route = source[entry:end]
        self.assertLess(route.index("assert_patient_access"), route.index("panoramic_elite_generator.generate"))
        self.assertIn("FileResponse(", route)

    def test_real_pdf_has_written_bilan_but_zero_embedded_images(self):
        from jinja2 import Environment, FileSystemLoader
        from weasyprint import HTML
        from pypdf import PdfReader
        import io

        env = Environment(loader=FileSystemLoader(str(TEMPLATE.parent)), autoescape=True)
        template = env.get_template(TEMPLATE.name)
        # Synthetic ONLY; deliberately supply radiograph/cephalo/QR dummy
        # references: the template must not interpolate any of them.
        html = template.render(
            primary_color="#15345b", secondary_color="#718096",
            patient_nom="SYNTHETIQUE", patient_prenom="Test",
            patient_id=999999, patient_age=34,
            date_analyse="22/10/2026", doctor_name="Dr DEMONSTRATION",
            denture_type="Non documenté",
            categories=[
                {"name": "TECHNIQUE", "findings": ["Radiographie panoramique numérique."]},
                {"name": "OBSERVATIONS", "findings": ["Observation manuelle sur dent 36."]},
                {"name": "SYNTHÈSE", "findings": ["Constatations vérifiées par le praticien."]},
            ],
            pano_url="file:///secret-do-not-embed-panorama.png",
            cephalo_url="file:///secret-do-not-embed-cephalo.png",
            qr_code_base64="data:image/png;base64,SECRET-DO-NOT-EMBED",
            metrics=[{"name": "NOT-A-PANORAMIC-REPORT"}],
        )
        for forbidden in ("secret-do-not-embed", "NOT-A-PANORAMIC-REPORT", "<img"):
            self.assertNotIn(forbidden, html)
        pdf = HTML(string=html, base_url=str(TEMPLATE.parent)).write_pdf()
        reader = PdfReader(io.BytesIO(pdf))
        self.assertGreaterEqual(len(reader.pages), 1)
        combined = "\n".join(page.extract_text() or "" for page in reader.pages)
        for expected in ("SYNTHETIQUE", "Dr DEMONSTRATION",
                         "Observation manuelle sur dent 36",
                         "Constatations vérifiées par le praticien"):
            self.assertIn(expected, combined)
        for unwanted in ("NOT-A-PANORAMIC-REPORT", "Téléradiographie",
                         "Synthèse Céphalométrique", "Radiographie Panoramique\\n"):
            self.assertNotIn(unwanted, combined)
        for index, page in enumerate(reader.pages, 1):
            self.assertEqual(len(page.images), 0, f"PDF page {index} has image XObjects")
        self.assertNotIn(b"/Subtype /Image", pdf)


if __name__ == "__main__":
    unittest.main()
