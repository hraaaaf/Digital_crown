from __future__ import annotations

import re
from types import SimpleNamespace

from pypdf import PdfReader
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Paragraph

from backend.schemas.honoraires import HonorairesData, PaymentItem
from backend.services.generators.honoraires_gen import HonorairesGenerator


class _FakeBaseTemplate:
    premium_font = "Helvetica"
    premium_bold = "Helvetica-Bold"

    def update_active_fonts(self, config):
        return None

    def get_document_margins(self, config, page_width):
        from reportlab.lib.units import cm
        return 2.0 * cm, 2.5 * cm, 1.5 * cm, 1.5 * cm

    def get_adaptive_style(self, base_style, text, max_width, min_fs=6.5, max_fs=None):
        clean = re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ")
        current_width = stringWidth(clean, base_style.fontName, base_style.fontSize) if clean else 0
        new_fs = base_style.fontSize if current_width <= 0 else base_style.fontSize * (max_width / current_width)
        new_fs = max(new_fs, min_fs)
        if max_fs is not None:
            new_fs = min(new_fs, max_fs)
        elif new_fs > base_style.fontSize * 1.25:
            new_fs = base_style.fontSize * 1.25
        return ParagraphStyle(
            f"{base_style.name}_adaptive",
            parent=base_style,
            fontSize=new_fs,
            leading=new_fs * 1.2,
        )


def _generator(tmp_path):
    generator = HonorairesGenerator.__new__(HonorairesGenerator)
    generator.output_dir = str(tmp_path)
    generator.base_template = _FakeBaseTemplate()
    generator.styles = getSampleStyleSheet()
    generator._get_save_path = lambda patient, doc_type, data, doc_id=None: str(tmp_path / "honoraires.pdf")
    generator._create_header = lambda patient, data, p_color: Paragraph("PATIENT TEST", generator.styles["Normal"])
    generator._amount_to_words = lambda amount: "trente et un mille cinq cents dirhams"
    generator._draw_canvas = lambda *args, **kwargs: None
    return generator


def test_long_honoraires_pdf_is_multipage_complete_and_readable(tmp_path):
    generator = _generator(tmp_path)
    payments = [
        PaymentItem(
            acte=(
                "Réhabilitation coronaire adhésive très longue description clinique "
                f"contrôlée ligne {index + 1} avec plusieurs mots pour permettre le wrapping normal"
            ),
            dents=[11 + (index % 8)],
            montant=875,
            mode_reglement="EN ATTENTE" if index % 2 == 0 else "TPE",
        )
        for index in range(36)
    ]
    data = HonorairesData(payments=payments, is_global_note=False)

    path = generator.generate_note(SimpleNamespace(nom="TEST", prenom="Patient"), data)
    reader = PdfReader(path)
    texts = [page.extract_text() or "" for page in reader.pages]
    merged = "\n".join(texts)

    assert len(reader.pages) >= 2
    assert all("PAIEMENT" in text and "HONORAIRES" in text for text in texts)
    assert sum(text.count("Réhabilitation coronaire") for text in texts) == 36
    assert "TOTAL GÉNÉRAL" in merged
    assert "31500.00" in merged
    assert "EN ATTENTE" in merged


def test_global_honoraires_title_and_installment_section_are_explicit(tmp_path):
    generator = _generator(tmp_path)
    data = HonorairesData(
        payments=[PaymentItem(acte="Composite", dents=[16], montant=700, mode_reglement="EN ATTENTE")],
        is_global_note=True,
        installments=[{"label": "Versement 1", "date": "2026-09-01", "amount": 700}],
    )

    path = generator.generate_note(SimpleNamespace(nom="TEST", prenom="Patient"), data)
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)

    assert "NOTE D'HONORAIRES GLOBALE" in text
    assert "SUIVI DES RÈGLEMENTS" in text
    assert "Versement 1" in text


def test_unique_honoraires_never_renders_installment_section(tmp_path):
    generator = _generator(tmp_path)
    data = HonorairesData(
        payments=[PaymentItem(acte="Composite", dents=[16], montant=700, mode_reglement="EN ATTENTE")],
        is_global_note=False,
        installments=[{"label": "Ancien plan", "date": "2026-01-01", "amount": 700}],
    )
    assert data.installments == []

    path = generator.generate_note(SimpleNamespace(nom="TEST", prenom="Patient"), data)
    text = "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)

    assert "SUIVI DES RÈGLEMENTS" not in text
    assert "Ancien plan" not in text
