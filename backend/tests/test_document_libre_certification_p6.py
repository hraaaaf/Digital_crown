from datetime import date
from types import SimpleNamespace

import fitz
import pytest

from backend.services.generators.libre_gen import LibreGenerator


@pytest.mark.parametrize(
    ("page_size", "expected_width", "expected_height"),
    [
        ("A4", 595.28, 841.89),
        ("A5", 419.53, 595.28),
    ],
)
def test_libre_pdf_respects_requested_page_size(tmp_path, page_size, expected_width, expected_height):
    generator = LibreGenerator(str(tmp_path))
    patient = SimpleNamespace(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=date(1990, 5, 12),
    )
    data = SimpleNamespace(
        titre="Compte rendu",
        contenu="Texte libre du praticien.",
        page_size=page_size,
        alignment="justify",
        custom_patient=None,
        custom_date=None,
        hide_patient_header=False,
        doc_date=date(2026, 8, 16),
    )

    path = generator.generate(patient, data)
    pdf = fitz.open(path)
    try:
        rect = pdf[0].rect
        assert rect.width == pytest.approx(expected_width, abs=1.0)
        assert rect.height == pytest.approx(expected_height, abs=1.0)
    finally:
        pdf.close()


def test_libre_pdf_preserves_custom_recipient_date_and_markdown_table(tmp_path):
    generator = LibreGenerator(str(tmp_path))
    patient = SimpleNamespace(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=date(1990, 5, 12),
    )
    data = SimpleNamespace(
        titre="Lettre de suivi",
        contenu=(
            "Synthèse clinique.\n\n"
            "| Acte | Montant |\n"
            "|---|---|\n"
            "| Consultation | 300 MAD |"
        ),
        page_size="A4",
        alignment="left",
        custom_patient="Dr Nadia Exemple",
        custom_date="Rabat, le 16/08/2026",
        hide_patient_header=False,
        doc_date=date(2026, 8, 16),
    )

    path = generator.generate(patient, data)
    pdf = fitz.open(path)
    try:
        text = "\n".join(page.get_text() for page in pdf)
        assert "Dr Nadia Exemple" in text
        assert "Rabat, le 16/08/2026" in text
        assert "Acte" in text
        assert "Montant" in text
        assert "Consultation" in text
        assert "300 MAD" in text
    finally:
        pdf.close()
