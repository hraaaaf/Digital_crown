import hashlib
import inspect

import fitz
import pytest

from backend.services.far_ordonnance_bridge import FarOrdonnanceBridgePayload, FarPrescriptionLine
from backend.services.insurance_far_2021_1_profile import FAR_2021_1_DERIVED_TEMPLATE_SHA256
from backend.services.insurance_far_prescription_renderer import (
    _medication_text,
    _single_line,
    render_far_prescription_pdf,
)


def _payload() -> FarOrdonnanceBridgePayload:
    return FarOrdonnanceBridgePayload(
        patient_id=12,
        source_ordonnance_document_id=98,
        lines=(FarPrescriptionLine(
            name="MEDICAMENT TEST",
            dosage="500 mg",
            form="comprime",
            posology="1 cp matin et soir",
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


def test_renderer_rejects_unrepresentable_posology_without_truncation():
    with pytest.raises(ValueError, match="posology.*printable width"):
        _single_line("x" * 80, field="posology[0]", max_chars=58)


def test_v4_medication_line_matches_validated_visual_hierarchy():
    assert _medication_text(
        name="AMOXICILLINE",
        dosage="1 g",
        form="comprime",
    ) == "AMOXICILLINE 1 g - comprime"
    assert _medication_text(name="PARACETAMOL", dosage="", form="") == "PARACETAMOL"


def test_renderer_contract_is_theme_independent():
    source = inspect.getsource(render_far_prescription_pdf)
    assert "theme" not in source.lower()
    assert 'fontname="helv"' in source
