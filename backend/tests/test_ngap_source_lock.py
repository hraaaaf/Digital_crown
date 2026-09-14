from io import BytesIO

import pytest
from reportlab.pdfgen import canvas

from backend.services.ngap_reference import (
    DENTAL_NGAP_PRIMARY_PENDING,
    NgapReferenceStatus,
    lock_ngap_primary_pdf,
)


def _pdf(text: str) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 720, text)
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def test_primary_ngap_lock_requires_legal_identity_markers():
    binary = _pdf(
        "Arrete du ministre de la sante n 177-06 - "
        "nomenclature generale des actes professionnels"
    )

    locked = lock_ngap_primary_pdf(
        release=DENTAL_NGAP_PRIMARY_PENDING,
        pdf_bytes=binary,
        source_url="https://example.invalid/official-177-06.pdf",
    )

    assert locked.status == NgapReferenceStatus.VERIFIED_PRIMARY
    assert len(locked.source_hash or "") == 64
    assert locked.source_url.endswith("official-177-06.pdf")
    assert locked.entries == {}


def test_primary_ngap_lock_rejects_unrelated_pdf_even_if_valid_pdf():
    with pytest.raises(ValueError, match="identity markers"):
        lock_ngap_primary_pdf(
            release=DENTAL_NGAP_PRIMARY_PENDING,
            pdf_bytes=_pdf("Un autre texte reglementaire sans rapport"),
        )


def test_primary_ngap_lock_rejects_non_pdf():
    with pytest.raises(ValueError, match="not a PDF"):
        lock_ngap_primary_pdf(
            release=DENTAL_NGAP_PRIMARY_PENDING,
            pdf_bytes=b"not-pdf",
        )
