"""Atomicity guard for calibration persistence."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend import schemas
from backend.routers.cephalo_calibration_provenance import calibrate_analysis_with_provenance
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY


def test_evidence_failure_rolls_back_without_commit(monkeypatch):
    analysis = SimpleNamespace(
        id=44,
        patient_id=7,
        image_original_path="radio.jpg",
        landmarks_data=[{"id": "N", "x": 1.0, "y": 2.0}],
        angles_data={EVIDENCE_GRAPH_KEY: {"schema_version": "BROKEN"}},
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

    with pytest.raises(HTTPException) as exc:
        calibrate_analysis_with_provenance(
            44,
            req,
            db=db,
            current_user=SimpleNamespace(id=99),
        )

    assert exc.value.status_code == 400
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
