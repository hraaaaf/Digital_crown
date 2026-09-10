import datetime as dt
from dataclasses import replace

import pytest

from backend.services.cephalo_auto_calibration_evidence import (
    AutoCalibrationEvidenceError,
    source_evidence_from_auto_decision,
)
from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationDecision,
    AutoCalibrationState,
    ValidatedFiducialProfile,
    evaluate_auto_calibration,
)
from backend.services.cephalo_calibration_candidate import CalibrationCandidate


def _verified_decision():
    candidate = CalibrationCandidate.from_ticks(
        axis_x_px=40,
        tick_positions_y_px=[10, 20, 30, 40, 50],
    )
    profile = ValidatedFiducialProfile(
        profile_id="TEST_RULER",
        version="1",
        known_tick_spacing_mm=10.0,
        min_ticks=5,
        max_spacing_deviation_ratio=0.05,
        validation_reference="test-fixture://validated-ruler-profile-v1",
    )
    return evaluate_auto_calibration(candidate, profile=profile)


def _recorded_at():
    return dt.datetime(2026, 9, 10, 20, 0, tzinfo=dt.timezone.utc)


def test_auto_verified_decision_materializes_distinct_typed_source():
    source = source_evidence_from_auto_decision(
        patient_id=12,
        image_record_id="radio-12.png",
        decision=_verified_decision(),
        recorded_at=_recorded_at(),
    )

    assert source.evidence_id == "src-calibration-auto-verified"
    assert source.kind == "calibration"
    assert source.operator_id is None
    assert source.quality_status == "AUTO_VERIFIED_FIDUCIAL_PROFILE"
    assert source.metadata["method"] == "AUTO_FIDUCIAL_PROFILE"
    assert source.metadata["clinician_confirmed"] is False
    assert source.metadata["validation_reference"].startswith("test-fixture://")
    assert source.metadata["mm_per_pixel"] == pytest.approx(1.0)


def test_candidate_unverified_decision_cannot_create_typed_calibration_source():
    decision = AutoCalibrationDecision(
        state=AutoCalibrationState.CANDIDATE_UNVERIFIED,
        reason="NO_VALIDATED_PHYSICAL_SCALE_SOURCE",
    )

    with pytest.raises(AutoCalibrationEvidenceError, match="AUTO_VERIFIED"):
        source_evidence_from_auto_decision(
            patient_id=12,
            image_record_id="radio-12.png",
            decision=decision,
            recorded_at=_recorded_at(),
        )


def test_forged_ratio_is_rejected():
    decision = _verified_decision()
    forged = replace(decision, mm_per_pixel=0.5)

    with pytest.raises(AutoCalibrationEvidenceError, match="ratio"):
        source_evidence_from_auto_decision(
            patient_id=12,
            image_record_id="radio-12.png",
            decision=forged,
            recorded_at=_recorded_at(),
        )


def test_missing_profile_reference_is_rejected():
    decision = _verified_decision()
    provenance = dict(decision.provenance)
    provenance["validation_reference"] = ""
    forged = replace(decision, provenance=provenance)

    with pytest.raises(AutoCalibrationEvidenceError, match="validation_reference"):
        source_evidence_from_auto_decision(
            patient_id=12,
            image_record_id="radio-12.png",
            decision=forged,
            recorded_at=_recorded_at(),
        )


def test_auto_source_cannot_claim_clinician_confirmation():
    decision = _verified_decision()
    provenance = dict(decision.provenance)
    provenance["clinician_confirmed"] = True
    forged = replace(decision, provenance=provenance)

    with pytest.raises(AutoCalibrationEvidenceError, match="clinician"):
        source_evidence_from_auto_decision(
            patient_id=12,
            image_record_id="radio-12.png",
            decision=forged,
            recorded_at=_recorded_at(),
        )


def test_naive_timestamp_is_rejected():
    with pytest.raises(AutoCalibrationEvidenceError, match="timezone-aware"):
        source_evidence_from_auto_decision(
            patient_id=12,
            image_record_id="radio-12.png",
            decision=_verified_decision(),
            recorded_at=dt.datetime(2026, 9, 10, 20, 0),
        )
