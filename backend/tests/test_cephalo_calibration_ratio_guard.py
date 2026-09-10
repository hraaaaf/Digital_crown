"""Manual calibration ratio contract."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from backend import schemas
from backend.routers.cephalo_calibration_provenance import calibrate_analysis_with_provenance


def test_points_too_close_are_rejected_before_persistence(monkeypatch):
    analysis = SimpleNamespace(id=1, patient_id=7)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = analysis
    monkeypatch.setattr(
        "backend.routers.cephalo_calibration_provenance.assert_patient_access",
        lambda *_args, **_kwargs: None,
    )
    req = schemas.CalibrationRequest(
        p1=schemas.CalibrationPoint(x=0.0, y=0.0),
        p2=schemas.CalibrationPoint(x=0.0, y=4.0),
        distance_mm=10.0,
    )

    with pytest.raises(HTTPException) as exc:
        calibrate_analysis_with_provenance(
            1, req, db=db, current_user=SimpleNamespace(id=99)
        )

    assert exc.value.status_code == 400
    db.commit.assert_not_called()
