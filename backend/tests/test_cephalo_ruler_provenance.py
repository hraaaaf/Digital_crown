from types import SimpleNamespace

from backend.schemas.clinical import CalibrationPoint, CalibrationRequest
from backend.routers.cephalo_calibration_provenance import (
    _confirmed_ruler_candidate,
    _promote_calibration_source,
)


def _analysis(candidate):
    return SimpleNamespace(calibration_data=candidate)


def _request(p1=(620.0, 55.0), p2=(620.0, 80.0)):
    return CalibrationRequest(
        p1=CalibrationPoint(x=p1[0], y=p1[1]),
        p2=CalibrationPoint(x=p2[0], y=p2[1]),
        distance_mm=10.0,
    )


def _candidate():
    return {
        "schema_version": "CEPHALO_CALIBRATION_CANDIDATE_V1",
        "method": "RULER_TICK_CANDIDATE_V1",
        "p1": [620.0, 55.0],
        "p2": [620.0, 80.0],
        "distance_px": 25.0,
        "tick_count": 6,
        "spacing_regularity": 1.0,
        "requires_clinician_validation": True,
        "verification_status": "UNVERIFIED",
    }


def test_matching_persisted_candidate_is_recognized_as_ruler_confirmation():
    assert _confirmed_ruler_candidate(_analysis(_candidate()), _request()) is True


def test_edited_candidate_points_become_manual_calibration():
    assert _confirmed_ruler_candidate(
        _analysis(_candidate()),
        _request(p2=(620.0, 82.0)),
    ) is False


def test_ruler_confirmation_promotes_typed_calibration_source_without_touching_others():
    payload = {
        "sources": [
            {"kind": "lateral_ceph", "quality_status": "SOURCE"},
            {
                "kind": "calibration",
                "quality_status": "VERIFIED_MANUAL_TWO_POINT",
                "metadata": {"method": "MANUAL_TWO_POINT", "method_version": "1"},
            },
        ]
    }

    promoted = _promote_calibration_source(payload, ruler_candidate=True)

    assert promoted["sources"][0]["quality_status"] == "SOURCE"
    calibration = promoted["sources"][1]
    assert calibration["quality_status"] == "VERIFIED_RULER_FIDUCIAL"
    assert calibration["metadata"]["method"] == "RULER_TICK_CANDIDATE_V1"
    assert calibration["metadata"]["clinician_confirmation"] is True
