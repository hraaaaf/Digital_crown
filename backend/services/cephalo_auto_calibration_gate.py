"""Objective gate for automatic cephalometric fiducial calibration.

Automatic verification is allowed only when image-space geometry is combined with
an explicitly validated physical-scale profile. No default millimetre spacing or
quality threshold exists in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from backend.services.cephalo_calibration_candidate import CalibrationCandidate


class AutoCalibrationState(str, Enum):
    CANDIDATE_UNVERIFIED = "CANDIDATE_UNVERIFIED"
    AUTO_VERIFIED = "AUTO_VERIFIED"
    CLINICIAN_CONFIRMED = "CLINICIAN_CONFIRMED"


@dataclass(frozen=True)
class ValidatedFiducialProfile:
    """Versioned physical ruler profile approved outside the detector itself."""

    profile_id: str
    version: str
    known_tick_spacing_mm: float
    min_ticks: int
    max_spacing_deviation_ratio: float
    validation_reference: str

    def __post_init__(self) -> None:
        if not self.profile_id.strip() or not self.version.strip():
            raise ValueError("fiducial profile id and version are required")
        if not self.validation_reference.strip():
            raise ValueError("validated physical-scale source reference is required")
        if not math.isfinite(self.known_tick_spacing_mm) or self.known_tick_spacing_mm <= 0:
            raise ValueError("known tick spacing must be finite and positive")
        if self.min_ticks < 2:
            raise ValueError("min_ticks must be at least 2")
        if (
            not math.isfinite(self.max_spacing_deviation_ratio)
            or self.max_spacing_deviation_ratio < 0
            or self.max_spacing_deviation_ratio >= 1
        ):
            raise ValueError("max spacing deviation ratio must be in [0, 1)")


@dataclass(frozen=True)
class AutoCalibrationDecision:
    state: AutoCalibrationState
    reason: str
    mm_per_pixel: float | None = None
    provenance: dict[str, object] | None = None


def _max_spacing_deviation_ratio(candidate: CalibrationCandidate) -> float:
    ticks = candidate.tick_positions_y_px
    spacings = [b - a for a, b in zip(ticks, ticks[1:])]
    median = candidate.median_tick_spacing_px
    return max(abs(spacing - median) / median for spacing in spacings)


def evaluate_auto_calibration(
    candidate: CalibrationCandidate,
    *,
    profile: ValidatedFiducialProfile | None,
) -> AutoCalibrationDecision:
    """Evaluate whether a candidate may become AUTO_VERIFIED.

    With no validated physical profile, detection stays unverified. Thresholds are
    profile-owned and versioned; this gate intentionally carries no clinical defaults.
    """
    if profile is None:
        return AutoCalibrationDecision(
            state=AutoCalibrationState.CANDIDATE_UNVERIFIED,
            reason="NO_VALIDATED_PHYSICAL_SCALE_SOURCE",
        )

    tick_count = len(candidate.tick_positions_y_px)
    if tick_count < profile.min_ticks:
        return AutoCalibrationDecision(
            state=AutoCalibrationState.CANDIDATE_UNVERIFIED,
            reason="INSUFFICIENT_TICKS_FOR_PROFILE",
        )

    deviation_ratio = _max_spacing_deviation_ratio(candidate)
    if deviation_ratio > profile.max_spacing_deviation_ratio:
        return AutoCalibrationDecision(
            state=AutoCalibrationState.CANDIDATE_UNVERIFIED,
            reason="TICK_GEOMETRY_OUTSIDE_PROFILE_TOLERANCE",
        )

    mm_per_pixel = profile.known_tick_spacing_mm / candidate.median_tick_spacing_px
    if not math.isfinite(mm_per_pixel) or mm_per_pixel <= 0:
        return AutoCalibrationDecision(
            state=AutoCalibrationState.CANDIDATE_UNVERIFIED,
            reason="INVALID_DERIVED_SCALE",
        )

    provenance = {
        "schema_version": "CEPHALO_AUTO_CALIBRATION_V1",
        "state": AutoCalibrationState.AUTO_VERIFIED.value,
        "detector_method": candidate.detector_method,
        "profile_id": profile.profile_id,
        "profile_version": profile.version,
        "validation_reference": profile.validation_reference,
        "known_tick_spacing_mm": profile.known_tick_spacing_mm,
        "candidate_tick_count": tick_count,
        "median_tick_spacing_px": candidate.median_tick_spacing_px,
        "max_spacing_deviation_ratio": deviation_ratio,
        "profile_max_spacing_deviation_ratio": profile.max_spacing_deviation_ratio,
        "mm_per_pixel": mm_per_pixel,
        "clinician_confirmed": False,
    }
    return AutoCalibrationDecision(
        state=AutoCalibrationState.AUTO_VERIFIED,
        reason="VALIDATED_PROFILE_AND_GEOMETRY_GATES_PASSED",
        mm_per_pixel=mm_per_pixel,
        provenance=provenance,
    )
