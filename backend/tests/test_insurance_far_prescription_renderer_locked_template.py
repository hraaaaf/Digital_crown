from pathlib import Path

import fitz
import pytest

from backend.services.far_ordonnance_bridge import FarOrdonnanceBridgePayload, FarPrescriptionLine
from backend.services.insurance_far_2021_1_profile import FAR_2021_1_DERIVED_TEMPLATE_SHA256
from backend.services.insurance_far_prescription_renderer import render_far_prescription_pdf


def _payload(*, posology: str) -> FarOrdonnanceBridgePayload:
    return FarOrdonnanceBridgePayload(
        patient_id=12,
        source_ordonnance_document_id=98,
        lines=(FarPrescriptionLine(name="MEDICAMENT TEST", dosage="500 mg", form="comprime", posology=posology),),
    )


def test_locked_template_overflow_fails_closed(monkeypatch, tmp_path: Path):
    document = fitz.open()
    document.new_page(width=841.89, height=595.276)
    document.new_page(width=841.89, height=595.276)
    template = document.tobytes()
    document.close()

    import backend.services.insurance_far_prescription_renderer as renderer
    import hashlib
    monkeypatch.setattr(renderer, "FAR_2021_1_DERIVED_TEMPLATE_SHA256", hashlib.sha256(template).hexdigest())

    with pytest.raises(ValueError, match="posology.*printable width"):
        render_far_prescription_pdf(
            template_bytes=template,
            payload=_payload(posology="x" * 80),
            patient_full_name="Patient Test",
        )
