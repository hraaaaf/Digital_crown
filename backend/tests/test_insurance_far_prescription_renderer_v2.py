import hashlib

import fitz
import pytest

from backend.services.far_ordonnance_bridge import FarOrdonnanceBridgePayload, FarPrescriptionLine
import backend.services.insurance_far_prescription_renderer as renderer


def test_renderer_checks_overflow_after_template_identity(monkeypatch):
    document = fitz.open()
    document.new_page(width=841.89, height=595.276)
    document.new_page(width=841.89, height=595.276)
    template = document.tobytes()
    document.close()
    monkeypatch.setattr(
        renderer,
        "FAR_2021_1_DERIVED_TEMPLATE_SHA256",
        hashlib.sha256(template).hexdigest(),
    )
    payload = FarOrdonnanceBridgePayload(
        patient_id=12,
        source_ordonnance_document_id=98,
        lines=(FarPrescriptionLine(
            name="MEDICAMENT TEST",
            dosage="500 mg",
            form="comprime",
            posology="x" * 80,
        ),),
    )
    with pytest.raises(ValueError, match="posology.*printable width"):
        renderer.render_far_prescription_pdf(
            template_bytes=template,
            payload=payload,
            patient_full_name="Patient Test",
        )
