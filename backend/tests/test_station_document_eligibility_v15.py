from types import SimpleNamespace

import pytest

from backend import models
from backend.services.station_document_eligibility import station_document_eligibility


def _doc(**overrides):
    values = {
        "patient_id": 41,
        "status": models.DocumentStatus.ACTIF,
        "deleted_at": None,
        "is_latest_version": True,
        "document_type": models.DocumentType.CERTIFICAT,
        "clinical_data": {
            "station_self_service": {
                "eligible": True,
                "kind": "attendance_certificate",
            }
        },
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"patient_id": 99}, "PATIENT_MISMATCH"),
        ({"status": models.DocumentStatus.ARCHIVE}, "DOCUMENT_NOT_ACTIVE"),
        ({"deleted_at": object()}, "DOCUMENT_NOT_ACTIVE"),
        ({"is_latest_version": False}, "DOCUMENT_NOT_LATEST"),
        ({"document_type": models.DocumentType.ORDONNANCE}, "DOCUMENT_TYPE_NOT_ALLOWED"),
        ({"clinical_data": None}, "EXPLICIT_ELIGIBILITY_REQUIRED"),
        ({"clinical_data": {}}, "EXPLICIT_ELIGIBILITY_REQUIRED"),
        ({"clinical_data": {"station_self_service": {"eligible": False, "kind": "attendance_certificate"}}}, "EXPLICIT_ELIGIBILITY_REQUIRED"),
        ({"clinical_data": {"station_self_service": {"eligible": True, "kind": "unknown"}}}, "DOCUMENT_KIND_NOT_ALLOWED"),
    ],
)
def test_station_document_eligibility_fails_closed(overrides, reason):
    result = station_document_eligibility(_doc(**overrides), patient_id=41)

    assert result.eligible is False
    assert result.reason == reason


def test_station_document_eligibility_accepts_explicit_attendance_certificate():
    result = station_document_eligibility(_doc(), patient_id=41)

    assert result.eligible is True
    assert result.kind == "attendance_certificate"
    assert result.reason is None


def test_station_document_eligibility_accepts_explicit_care_sheet_only_when_whitelisted_type():
    result = station_document_eligibility(
        _doc(
            document_type=models.DocumentType.AUTRE,
            clinical_data={
                "station_self_service": {
                    "eligible": True,
                    "kind": "care_sheet",
                }
            },
        ),
        patient_id=41,
    )

    assert result.eligible is True
    assert result.kind == "care_sheet"
