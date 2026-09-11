"""Repository-level calibration invariants for R1."""
import inspect
from types import SimpleNamespace

from backend.repositories.cephalo_repository import (
    CephaloRepository,
    _merge_calibration_projection,
)


def test_create_has_no_implicit_mm_per_pixel_default():
    parameter = inspect.signature(CephaloRepository.create).parameters["mm_per_pixel"]
    assert parameter.default is None


def test_ordinary_save_preserves_auto_verified_projection_and_evidence_labels():
    previous = {
        "calibration_status": "auto_verified",
        "calibration_candidate": {"status": "CANDIDATE_UNVERIFIED", "axis_x_px": 42.0},
        "calibration_decision": {"state": "AUTO_VERIFIED", "profile_id": "RULER_V1"},
        "metrics": {"old": True},
    }
    recomputed = {
        "calibration_status": "verified",
        "metrics": {"new": True},
    }

    merged = _merge_calibration_projection(previous, recomputed)

    assert merged["calibration_status"] == "auto_verified"
    assert merged["calibration_candidate"] == previous["calibration_candidate"]
    assert merged["calibration_decision"] == previous["calibration_decision"]
    assert merged["metrics"] == {"new": True}


def test_ordinary_save_preserves_clinician_confirmed_projection():
    previous = {
        "calibration_status": "clinician_confirmed",
        "calibration_decision": {"state": "CLINICIAN_CONFIRMED"},
    }
    merged = _merge_calibration_projection(previous, {"calibration_status": "verified"})

    assert merged["calibration_status"] == "clinician_confirmed"
    assert merged["calibration_decision"]["state"] == "CLINICIAN_CONFIRMED"


def test_manual_or_unverified_projection_is_not_promoted_by_repository_merge():
    assert _merge_calibration_projection(
        {"calibration_status": "unverified"},
        {"calibration_status": "unverified"},
    )["calibration_status"] == "unverified"

    assert _merge_calibration_projection(
        {"calibration_status": "verified"},
        {"calibration_status": "verified"},
    )["calibration_status"] == "verified"


def test_update_uses_calibration_safe_projection_merge(monkeypatch):
    analysis = SimpleNamespace(
        landmarks_data=[],
        angles_data={
            "calibration_status": "auto_verified",
            "calibration_decision": {"state": "AUTO_VERIFIED"},
        },
        mm_per_pixel=0.2,
    )
    db = SimpleNamespace(commit=lambda: None, refresh=lambda _obj: None)
    repo = CephaloRepository(db)
    monkeypatch.setattr(repo, "get_by_id", lambda _analysis_id: analysis)

    updated = repo.update(
        7,
        [{"id": "S", "x": 1.0, "y": 2.0}],
        {"calibration_status": "verified", "metrics": {}},
        mm_per_pixel=0.2,
    )

    assert updated is analysis
    assert analysis.angles_data["calibration_status"] == "auto_verified"
    assert analysis.angles_data["calibration_decision"]["state"] == "AUTO_VERIFIED"
