"""LOT05/J10G: dentist-entered FDI table in existing patient PDF, no AI inference."""
import unittest
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from backend.services.panoramic_fdi_report_rows import confirmed_manual_fdi_rows


class TestManualPanoramicFDIRows(unittest.TestCase):
    def test_explicit_manual_dentist_observations_only(self):
        result = confirmed_manual_fdi_rows({
            "detections": [{"tooth": 36, "pathology": "carie_dentinaire"}],
            "manual_anomalies": {"36": ["carie_dentinaire"], "37": ["tr_adequat"]},
        })
        self.assertEqual([r["fdi"] for r in result], ["36", "37"])
        self.assertTrue(all(r["provenance"] == "practitioner_manual_annotation" for r in result))
        self.assertIn("Carie dentinaire", result[0]["observations"])

    def test_nonmanual_ai_detections_never_render(self):
        self.assertEqual(confirmed_manual_fdi_rows({
            "detections": [{"tooth": 36, "label": "suspicious_carious_tooth"}]
        }), [])

    def test_out_of_range_and_unknown_findings_not_fabricated(self):
        result = confirmed_manual_fdi_rows({"manual_anomalies": {
            "55": ["carie_dentinaire"], "10": ["carie_dentinaire"],
            "36": ["NOT_REAL_CODE"], "37": ["tr_adequat", "tr_adequat"]
        }})
        self.assertEqual([r["fdi"] for r in result], ["37"])
        self.assertEqual(len(result[0]["observations"]), 1)

    def test_invalid_or_missing_input_results_in_no_clinical_assumptions(self):
        self.assertEqual(confirmed_manual_fdi_rows({}), [])
        self.assertEqual(confirmed_manual_fdi_rows(None), [])
        self.assertEqual(confirmed_manual_fdi_rows({"manual_anomalies": ["16"]}), [])

    def test_pdf_template_renders_tooth_table_only_if_manual_fdi(self):
        path = Path("backend/templates")
        env = Environment(loader=FileSystemLoader(str(path)), autoescape=select_autoescape(["html"]))
        templ = env.get_template("panoramic_elite.html")
        base = {
            "primary_color":"#103454", "secondary_color":"#52677a",
            "patient_nom":"SYNTHETIQUE","patient_prenom":"PATIENT",
            "patient_id":"DEMO", "date_analyse":"22/10/2026", "patient_age":"N/A",
            "doctor_name":"Dr Exemple", "denture_type":"Non documenté",
            "pano_url":None, "cephalo_url":None, "categories":[], "metrics":[],
            "qr_code_base64":None,
        }
        missing = templ.render(**{**base, "manual_fdi_rows":[]})
        self.assertNotIn("Détail des constatations documentées dent par dent", missing)
        with_teeth = templ.render(**{**base, "manual_fdi_rows": [
            {"fdi":"36","observations":["Élément dentaire documenté par le praticien"]},
        ]})
        self.assertIn("Détail des constatations documentées dent par dent", with_teeth)
        self.assertIn("Élément dentaire documenté", with_teeth)
        self.assertIn("Les autres dents ne sont pas évaluées", with_teeth)


if __name__ == "__main__":
    unittest.main()
