"""Regression tests for installment receipt PDF pagination/readability."""
from datetime import date

from pypdf import PdfReader

from backend.services.generators.installment_receipt_gen import generate_installment_receipt


def _items(count: int):
    return [
        {
            "label": f"Échéance {i + 1}",
            "amount": 300.0,
            "due_date": date(2027 + i // 12, (i % 12) + 1, 15).isoformat(),
            "paid": i < max(1, count // 4),
        }
        for i in range(count)
    ]


def test_dense_installment_pdf_keeps_summary(tmp_path):
    path = generate_installment_receipt(patient_name="PDF TEST Élodie", title="Plan de paiement dense", total_amount=3600.0, items=_items(12), output_dir=str(tmp_path))
    reader = PdfReader(path)
    assert len(reader.pages) >= 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "SUIVI DE PAIEMENT" in text
    assert "Plan de paiement dense" in text
    assert "3600.00 MAD" in text
    assert "2700.00 MAD" in text
    assert len(reader.pages) == 2
    page_2_text = reader.pages[1].extract_text() or ""
    # Regression guard: P2 must contain a coherent tail block, not a single
    # orphan installment followed by totals.
    for label in ("Échéance 9", "Échéance 10", "Échéance 11", "Échéance 12"):
        assert label in page_2_text
    assert "TOTAL RÉGLÉ" in page_2_text


def test_stress_installment_pdf_keeps_all_rows_and_summary(tmp_path):
    path = generate_installment_receipt(patient_name="PDF TEST Élodie", title="Plan long — Échéancier robustesse", total_amount=7200.0, items=_items(24), output_dir=str(tmp_path))
    reader = PdfReader(path)
    assert len(reader.pages) >= 2
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Échéance 1" in text
    assert "Échéance 24" in text
    assert "7200.00 MAD" in text
