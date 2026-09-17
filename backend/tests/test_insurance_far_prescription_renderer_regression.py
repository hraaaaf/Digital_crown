import pytest

from backend.services.far_ordonnance_bridge import FarOrdonnanceBridgePayload, FarPrescriptionLine
from backend.services.insurance_far_prescription_renderer import render_far_prescription_pdf


def test_invalid_template_fails_before_content_validation():
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
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        render_far_prescription_pdf(
            template_bytes=b"not-the-locked-template",
            payload=payload,
            patient_full_name="Patient Test",
        )
