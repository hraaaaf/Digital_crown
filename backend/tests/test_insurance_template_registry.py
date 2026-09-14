from io import BytesIO

import pytest
from reportlab.pdfgen import canvas

from backend.services.insurance_template_registry import (
    CNSS_610_1_04,
    lock_template_pdf,
)


def _pdf(page_count: int) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    for index in range(page_count):
        pdf.drawString(72, 720, f"Template test page {index + 1}")
        pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def test_cnss_template_lock_records_exact_hash_and_page_count():
    binary = _pdf(2)
    locked = lock_template_pdf(
        definition=CNSS_610_1_04,
        pdf_bytes=binary,
        source_url="https://example.invalid/cnss-610-1-04.pdf",
    )

    assert locked.page_count == 2
    assert len(locked.sha256) == 64
    snapshot = locked.as_submission_snapshot()
    assert snapshot.template_version == "CNSS-610-1-04"
    assert snapshot.template_hash == locked.sha256


def test_cnss_template_lock_rejects_wrong_page_count():
    with pytest.raises(ValueError, match="page count mismatch"):
        lock_template_pdf(
            definition=CNSS_610_1_04,
            pdf_bytes=_pdf(1),
            source_url="https://example.invalid/wrong.pdf",
        )


def test_template_lock_rejects_non_pdf_or_missing_provenance():
    with pytest.raises(ValueError, match="not a PDF"):
        lock_template_pdf(
            definition=CNSS_610_1_04,
            pdf_bytes=b"not-pdf",
            source_url="https://example.invalid/not.pdf",
        )

    with pytest.raises(ValueError, match="provenance"):
        lock_template_pdf(
            definition=CNSS_610_1_04,
            pdf_bytes=_pdf(2),
            source_url="",
        )
