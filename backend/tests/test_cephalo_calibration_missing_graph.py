"""Legacy analyses must remain calibratable without invented evidence history."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend import schemas
from backend.routers.cephalo_calibration_provenance import calibrate_analysis_with_provenance
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def test_missing_evidence_graph_is_not_backfilled(monkeypatch):
    analysis = SimpleNamespace(
        id=60,
        patient_id=7,
        image_original_path="legacy.jpg",
        landmarks_data=[
            {"id": "S", "x": 10.0, "y": 10.0},
            {"id": "N", "x": 20.0, "y": 10.0},
            {"id": "Po", "x": 0.0, "y": 20.0},
            {"id": "Or", "x": 20.0, "y": 20.0},
            {"id": "A", "x": 24.0, "y": 28.0},
            {"id": "B", "x": 22.0, "y": 38.0},
        ],
        angles_data={},
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

    calibrate_analysis_with_provenance(60, req, db=db, current_user=SimpleNamespace(id=99))

    assert EVIDENCE_GRAPH_KEY not in analysis.angles_data
    assert analysis.calibration_data["schema_version"] == "CEPHALO_CALIBRATION_V1"
