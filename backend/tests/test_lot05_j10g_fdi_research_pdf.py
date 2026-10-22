"""LOT05/J10G: real PDF generation with invented non-patient synthetic images only."""
from __future__ import annotations

from io import BytesIO
import unittest

from PIL import Image, ImageDraw
from pypdf import PdfReader

from backend.services.generators.fdi_research_pdf import (
    FDIReportError, VERSION, render_research_pdf, validate_report_data,
)


def sample_image() -> bytes:
    image = Image.new("RGB", (1200, 600), "#223342")
    draw = ImageDraw.Draw(image)
    for i in range(8):
        x = 150 + 120 * i
        draw.ellipse((x-35, 205, x+35, 395), fill="#98a8b2")
    out = BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


def draft():
    return {
        "schema": VERSION,
        "clinical_status": "RESEARCH_ONLY_NOT_SAVED_TO_PATIENT",
        "clinic": {"name": "Cabinet de démonstration fictif"},
        "patient": {"display_name": "PATIENT SYNTHÉTIQUE", "record_ref": "DEMO-0001"},
        "exam": {"date": "2026-10-22", "reference": "DEMO-PANO-001"},
        "reviewer": {"display_name": "Praticien de démonstration", "reviewed_at": None},
        "clinician_review_confirmed": False,
        "practitioner_summary": "Observation fictive saisie par un humain pour une démonstration.",
        "teeth": [
            {
                "fdi": "36", "bbox": [0.2, 0.31, 0.27, 0.68], "confirmed": True,
                "practitioner_observations": ["Observation manuelle fictive pour 36."],
                "manually_selected_acts": [{
                    "specialty": "Endodontie", "label": "Acte choisi à titre d'exemple",
                    "selected_by_clinician": True,
                }],
            },
            {
                "fdi": "37", "bbox": [0.31, 0.31, 0.38, 0.68], "confirmed": True,
                "practitioner_observations": [],
                "manually_selected_acts": [],
            },
        ],
    }


class TestFDIPdf(unittest.TestCase):
    def test_pdf_valid_research_draft(self):
        data = render_research_pdf(draft(), sample_image())
        self.assertTrue(data.startswith(b"%PDF-"))
        document = PdfReader(BytesIO(data))
        self.assertGreaterEqual(len(document.pages), 1)
        all_text = "\n".join((p.extract_text() or "") for p in document.pages)
        for word in ("PATIENT SYNTH", "DEMO-0001", "36", "37",
                     "Endodontie", "NON FINALIS", "RECHERCHE"):
            self.assertIn(word, all_text.upper() if word.isupper() else all_text)
        self.assertNotIn("carie automatiquement détectée", all_text.lower())
        self.assertNotIn("Aucune anomalie", all_text)

    def test_explicit_review_metadata_rendered_only_when_declared(self):
        sample = draft()
        sample["clinician_review_confirmed"] = True
        sample["reviewer"]["reviewed_at"] = "2026-10-22 15:30"
        pdf = PdfReader(BytesIO(render_research_pdf(sample, sample_image())))
        all_text = "\n".join(p.extract_text() for p in pdf.pages)
        self.assertIn("2026-10-22 15:30", all_text)
        self.assertNotIn("RELECTURE NON FINALIS", all_text)

    def test_not_allowed_to_add_model_suggested_act(self):
        sample = draft()
        sample["teeth"][0]["manually_selected_acts"][0]["selected_by_clinician"] = False
        with self.assertRaisesRegex(FDIReportError, "unverified_auto_act_forbidden"):
            render_research_pdf(sample, sample_image())

    def test_not_allowed_to_publish_unconfirmed_model_tooth(self):
        sample = draft()
        sample["teeth"][0]["confirmed"] = False
        with self.assertRaisesRegex(FDIReportError, "unconfirmed_tooth_in_report"):
            render_research_pdf(sample, sample_image())

    def test_not_allowed_to_publish_duplicate_or_primary_fdi(self):
        sample = draft()
        sample["teeth"][1]["fdi"] = "36"
        with self.assertRaisesRegex(FDIReportError, "invalid_or_duplicate_permanent_fdi"):
            render_research_pdf(sample, sample_image())
        sample["teeth"][1]["fdi"] = "55"
        with self.assertRaisesRegex(FDIReportError, "invalid_or_duplicate_permanent_fdi"):
            render_research_pdf(sample, sample_image())

    def test_invalid_image_or_out_of_bounds(self):
        sample = draft()
        with self.assertRaises(FDIReportError):
            render_research_pdf(sample, b"not-an-image")
        sample["teeth"][0]["bbox"] = [-.2, .3, .3, .7]
        with self.assertRaisesRegex(FDIReportError, "out_of_frame_tooth_box"):
            render_research_pdf(sample, sample_image())

    def test_forbid_unapproved_clinical_status(self):
        sample = draft()
        sample["clinical_status"] = "CLINICAL_APPROVED"
        with self.assertRaisesRegex(FDIReportError, "clinical_activation_not_authorized"):
            render_research_pdf(sample, sample_image())

    def test_no_implicit_assumptions_for_empty_observations(self):
        sample = draft()
        sample["teeth"][0]["practitioner_observations"] = []
        sample["teeth"][0]["manually_selected_acts"] = []
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(
            render_research_pdf(sample, sample_image())
        )).pages)
        self.assertIn("Aucune observation saisie", text)
        self.assertNotIn("Dent saine", text)

    def test_render_escapes_practitioner_html(self):
        sample = draft()
        sample["practitioner_summary"] = "<strong>NOT A TAG</strong> & visible."
        text = "\n".join(p.extract_text() for p in PdfReader(BytesIO(
            render_research_pdf(sample, sample_image())
        )).pages)
        self.assertIn("<strong>NOT A TAG</strong>", text)
        self.assertIn("& visible", text)

    def test_report_creation_is_separate_from_patient_routes(self):
        import inspect
        from backend.services.generators import fdi_research_pdf
        text = inspect.getsource(fdi_research_pdf)
        for forbidden in ("api.post(", "requests.post(", "sqlalchemy", "update_patient", "download_model"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
