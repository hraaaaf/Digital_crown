from datetime import date
from types import SimpleNamespace

import fitz

from backend.services.generators.libre_gen import LibreGenerator


def test_title_with_ampersand_and_angle_brackets_generates_readable_pdf(tmp_path):
    generator = LibreGenerator(str(tmp_path))
    patient = SimpleNamespace(
        nom="EL ALAMI",
        prenom="Youssef",
        date_naissance=date(1990, 5, 12),
    )
    data = SimpleNamespace(
        titre="R&D <suivi>",
        contenu="Texte libre du praticien.",
        page_size="A5",
        alignment="justify",
        custom_patient=None,
        custom_date=None,
        hide_patient_header=False,
        doc_date=date(2026, 8, 16),
    )

    path = generator.generate(patient, data)
    pdf = fitz.open(path)
    try:
        text = "\n".join(page.get_text() for page in pdf)
        assert "R&D <SUIVI>" in text
    finally:
        pdf.close()
