"""Typed contract for an unverified cephalometric fiducial calibration candidate.

A candidate describes image-space geometry only. It MUST NOT imply a physical
millimetre scale, verified calibration, or clinician acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


class CalibrationCandidateError(ValueError):
    """Raised when detected candidate geometry is malformed."""


@dataclass(frozen=True)
class CalibrationCandidate:
    """Unverified ruler/fiducial candidate in original image coordinates."""

    axis_x_px: float
    tick_positions_y_px: tuple[float, ...]
    median_tick_spacing_px: float
    detector_method: str = "CLASSICAL_RULER_GEOMETRY_V1"

    @classmethod
    def from_ticks(
        cls,
        *,
        axis_x_px: float,
        tick_positions_y_px: Sequence[float],
    ) -> "CalibrationCandidate":
        axis = float(axis_x_px)
        ticks = tuple(float(value) for value in tick_positions_y_px)
        if not math.isfinite(axis):
            raise CalibrationCandidateError("axis_x_px must be finite")
        if len(ticks) < 2 or any(not math.isfinite(value) for value in ticks):
            raise CalibrationCandidateError("at least two finite tick positions are required")
        if any(b <= a for a, b in zip(ticks, ticks[1:])):
            raise CalibrationCandidateError("tick positions must be strictly increasing")
        spacings = sorted(b - a for a, b in zip(ticks, ticks[1:]))
        midpoint = len(spacings) // 2
        median = (
            spacings[midpoint]
            if len(spacings) % 2
            else (spacings[midpoint - 1] + spacings[midpoint]) / 2.0
        )
        if median <= 0 or not math.isfinite(median):
            raise CalibrationCandidateError("median tick spacing must be finite and positive")
        return cls(axis_x_px=axis, tick_positions_y_px=ticks, median_tick_spacing_px=median)

    def to_payload(self) -> dict[str, object]:
        """Serialize without inventing physical scale or validation state."""
        return {
            "status": "CANDIDATE_UNVERIFIED",
            "detector_method": self.detector_method,
            "axis_x_px": self.axis_x_px,
            "tick_positions_y_px": list(self.tick_positions_y_px),
            "median_tick_spacing_px": self.median_tick_spacing_px,
            "mm_per_pixel": None,
            "distance_mm": None,
            "clinician_validated": False,
        }
