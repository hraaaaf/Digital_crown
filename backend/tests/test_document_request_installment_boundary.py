import pytest
from pydantic import ValidationError

from backend import schemas


def test_exported_document_request_rejects_raw_installment_payload():
    with pytest.raises(ValidationError) as exc_info:
        schemas.DocumentRequest(
            type="echeancier",
            patient_id=1,
            data={
                "title": "Plan brut",
                "totalAmount": 1000,
                "items": [{"label": "Versement", "amount": 1000}],
            },
        )
    assert "installment_document_requires_saved_plan" in str(exc_info.value)


def test_exported_document_request_accepts_saved_installment_reference():
    request = schemas.DocumentRequest(
        type="echeancier",
        patient_id=1,
        data={"plan_id": 42},
    )
    assert request.data["plan_id"] == 42
