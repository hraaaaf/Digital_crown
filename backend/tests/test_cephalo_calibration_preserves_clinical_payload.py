"""Compatibility guard: calibration updates geometry without erasing authored clinical payload."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend import schemas
from backend.routers.cephalo_calibration_provenance import calibrate_analysis_with_provenance


def test_legacy_authored_fields_are_preserved(monkeypatch):
    raw = [
        {"id": "S", "x": 10.0, "y": 10.0},
        {"id": "N", "x": 20.0, "y": 10.0},
        {"id": "Po", "x": 0.0, "y": 20.0},
        {"id": "Or", "x": 20.0, "y": 20.0},
        {"id": "A", "x": 24.0, "y": 28.0},
        {"id": "B", "x": 22.0, "y": 38.0},
    ]
    authored = {"clinical_data": {"plan_traitement": "texte praticien"}, "ai_diagnostic": {"note": "praticien"}}
    analysis = SimpleNamespace(
        id=50,
        patient_id=7,
        image_original_path="legacy.jpg",
        landmarks_data=raw,
        angles_data=dict(authored),
        mm_per_pixel=None,
        is_calibrated=False,
        calibration_data=None,
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = analysis
    monkeypatch.setattr(
        "backend.routers.cephalo_calibration_provenance.assert_patient_access",
        lambda *_args, **_kwargs: None,
    )
    req = schemas.CalibrationRequest(
        p1=schemas.CalibrationPoint(x=0.0, y=0.0),
        p2=schemas.CalibrationPoint(x=0.0, y=50.0),
        distance_mm=10.0,
    )

    calibrate_analysis_with_provenance(50, req, db=db, current_user=SimpleNamespace(id=99))

    assert analysis.angles_data["clinical_data"] == authored["clinical_data"]
    assert analysis.angles_data["ai_diagnostic"] == authored["ai_diagnostic"]
    assert analysis.angles_data["analysis_metadata"]["pixel_ratio"] == 0.2
    assert analysis.angles_data["calibration_status"] == "verified"
