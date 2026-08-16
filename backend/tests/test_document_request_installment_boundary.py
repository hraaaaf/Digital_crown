import pytest
from pydantic import ValidationError

from backend import schemas


@pytest.mark.parametrize(
    "data",
    [
        {
            "title": "Plan brut",
            "totalAmount": 1000,
            "items": [{"label": "Versement", "amount": 1000}],
        },
        {"plan_id": 42},
    ],
)
def test_exported_document_request_rejects_legacy_installment_path(data):
    with pytest.raises(ValidationError) as exc_info:
        schemas.DocumentRequest(
            type="echeancier",
            patient_id=1,
            data=data,
        )
    assert "installment_document_path_disabled" in str(exc_info.value)
