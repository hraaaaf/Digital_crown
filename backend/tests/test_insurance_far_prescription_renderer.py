import hashlib

import fitz
import pytest

from backend.services.far_ordonnance_bridge import FarOrdonnanceBridgePayload, FarPrescriptionLine
from backend.services.insurance_far_2021_1_profile import FAR_2021_1_DERIVED_TEMPLATE_SHA256
from backend.services.insurance_far_prescription_renderer import render_far_prescription_pdf


def _payload(*, posology: str = "1 cp matin et soir") -> FarOrdonnanceBridgePayload:
    return FarOrdonnanceBridgePayload(
        patient_id=12,
        source_ordonnance_document_id=98,
        lines=(FarPrescriptionLine(
            name="MEDICAMENT TEST",
            dosage="500 mg",
            form="comprime",
            posology=posology,
        ),),
    )


def test_renderer_rejects_non_locked_template():
    document = fitz.open()
    document.new_page(width=841.89, height=595.276)
    document.new_page(width=841.89, height=595.276)
    arbitrary_pdf = document.tobytes()
    document.close()
    assert hashlib.sha256(arbitrary_pdf).hexdigest() != FAR_2021_1_DERIVED_TEMPLATE_SHA256
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        render_far_prescription_pdf(
            template_bytes=arbitrary_pdf,
            payload=_payload(),
            patient_full_name="Patient Test",
        )


def test_renderer_rejects_unrepresentable_posology_before_truncation():
    # Rendering must never silently truncate clinical prescription text.
    with pytest.raises(ValueError, match="posology.*printable width"):
        render_far_prescription_pdf(
            template_bytes=b"not-the-locked-template",
            payload=_payload(posology="x" * 80),
            patient_full_name="Patient Test",
        )


def test_renderer_contract_is_theme_independent():
    import inspect
    source = inspect.getsource(render_far_prescription_pdf)
    assert "theme" not in source.lower()
    assert 'fontname="helv"' in source
