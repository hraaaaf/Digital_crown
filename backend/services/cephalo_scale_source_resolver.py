"""Source-agnostic evidence resolver for commercial cephalometric scale.

Inputs are untrusted acquisition evidence, NOT permission to calibrate a patient.
DICOM PS3.3 (2026c) section 10.7 distinguishes calibrated patient Pixel Spacing,
detector Imager Pixel Spacing, and calibration type FIDUCIAL/GEOMETRY.

This module never publishes a physical scale from DICOM alone. Existing
authenticated server-side fiducial profile gates remain the only route for
automatic scale promotion; clinical measurements need a separate audited action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import re
from collections.abc import Mapping
from typing import Any

from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationState,
    ValidatedFiducialProfile,
    evaluate_auto_calibration,
)
from backend.services.cephalo_calibration_candidate import CalibrationCandidate


class ScaleSourceState(str, Enum):
    NO_PHYSICAL_SOURCE = "NO_PHYSICAL_SOURCE"
    IMAGE_RULER_UNVERIFIED = "IMAGE_RULER_UNVERIFIED"
    DICOM_REVIEW_REQUIRED = "DICOM_REVIEW_REQUIRED"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    FIDUCIAL_GATE_READY = "FIDUCIAL_GATE_READY"


class ScaleSourceReason(str, Enum):
    NO_EVIDENCE = "NO_EVIDENCE"
    RULER_WITHOUT_PROFILE = "RULER_WITHOUT_PROFILE"
    DICOM_PIXEL_SPACING_ABSENT = "DICOM_PIXEL_SPACING_ABSENT"
    DICOM_PIXEL_SPACING_INVALID = "DICOM_PIXEL_SPACING_INVALID"
    DICOM_CALIBRATION_UNATTESTED = "DICOM_CALIBRATION_UNATTESTED"
    DICOM_DESCRIPTION_MISSING = "DICOM_DESCRIPTION_MISSING"
    DICOM_PIXEL_GRID_UNATTESTED = "DICOM_PIXEL_GRID_UNATTESTED"
    DICOM_ANISOTROPIC_SPACING = "DICOM_ANISOTROPIC_SPACING"
    SOURCES_DISAGREE = "SOURCES_DISAGREE"
    SERVER_PROFILE_GATE_PASSED = "SERVER_PROFILE_GATE_PASSED"
    SERVER_PROFILE_GATE_FAILED = "SERVER_PROFILE_GATE_FAILED"


@dataclass(frozen=True)
class DicomScaleEvidence:
    """Untrusted metadata extracted by a future server-owned DICOM importer.

    Rows/Columns are the source *pixel matrix* dimensions (not image spacing).
    `rendered_rows/columns` refer to pixels currently used for landmark geometry.
    `source_verified` means a server verified the provenance of these tags, NOT
    that their clinical measurement plane was verified. No patient identifiers
    or arbitrary DICOM descriptions are ever included in the public result.
    """

    pixel_spacing: Any = None
    imager_pixel_spacing: Any = None
    nominal_scanned_pixel_spacing: Any = None
    calibration_type: str | None = None
    calibration_description: str | None = None
    source_rows: int | None = None
    source_columns: int | None = None
    rendered_rows: int | None = None
    rendered_columns: int | None = None
    source_verified: bool = False
    source_digest_sha256: str | None = None

    @classmethod
    def from_dicom_attributes(
        cls, attrs: Mapping[str, Any], *,
        rendered_rows: int | None = None,
        rendered_columns: int | None = None,
        source_verified: bool = False,
        source_digest_sha256: str | None = None,
    ) -> "DicomScaleEvidence":
        """Accept official DICOM tag strings OR keyword labels, never invent tags.

        Caller must separately decode pixel data and independently attest
        source_verified before this evidence can be interpreted as sourced.
        """
        def field(keyword: str, tag: str) -> Any:
            return attrs.get(keyword) if keyword in attrs else attrs.get(tag)

        return cls(
            pixel_spacing=field("PixelSpacing", "0028,0030"),
            imager_pixel_spacing=field("ImagerPixelSpacing", "0018,1164"),
            nominal_scanned_pixel_spacing=field("NominalScannedPixelSpacing", "0018,2010"),
            calibration_type=field("PixelSpacingCalibrationType", "0028,0A02"),
            calibration_description=field("PixelSpacingCalibrationDescription", "0028,0A04"),
            source_rows=field("Rows", "0028,0010"),
            source_columns=field("Columns", "0028,0011"),
            rendered_rows=rendered_rows,
            rendered_columns=rendered_columns,
            source_verified=source_verified,
            source_digest_sha256=source_digest_sha256,
        )


@dataclass(frozen=True)
class ScaleSourceResolution:
    state: ScaleSourceState
    reason: ScaleSourceReason
    source: str
    # Only server-side validated profiles may populate this preview.
    # It is NOT a clinically approved or persisted calibration.
    eligible_mm_per_pixel: float | None = None
    profile_id: str | None = None

    def to_payload(self) -> dict[str, object]:
        """Serializable, deliberately without patient data or a claimed scale."""
        return {
            "schema_version": "CEPHALO_SOURCE_RESOLUTION_V1",
            "state": self.state.value,
            "reason": self.reason.value,
            "source": self.source,
            "eligible_mm_per_pixel": self.eligible_mm_per_pixel,
            "profile_id": self.profile_id,
            "applied_to_analysis": False,
            "requires_server_promotion": True,
        }


def _spacing(value: Any) -> tuple[float, float] | None:
    if isinstance(value, str):
        parts = [v.strip() for v in value.split("\\")]
    elif isinstance(value, (list, tuple)):
        parts = value
    else:
        return None
    if len(parts) != 2:
        return None
    try:
        row, col = float(parts[0]), float(parts[1])
    except (TypeError, ValueError, OverflowError):
        return None
    if not (math.isfinite(row) and math.isfinite(col) and row > 0 and col > 0):
        return None
    return row, col


def _positive_int(value: Any) -> int | None:
    if type(value) is not int or value <= 0 or value > 50000:
        return None
    return value


def _dicom_reason(meta: DicomScaleEvidence) -> ScaleSourceReason:
    if meta.pixel_spacing is None:
        return ScaleSourceReason.DICOM_PIXEL_SPACING_ABSENT
    rowcol = _spacing(meta.pixel_spacing)
    if rowcol is None:
        return ScaleSourceReason.DICOM_PIXEL_SPACING_INVALID
    if not meta.source_verified or not re.fullmatch(r"[a-f0-9]{64}", meta.source_digest_sha256 or ""):
        return ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED
    shape = [_positive_int(x) for x in (
        meta.source_rows, meta.source_columns, meta.rendered_rows, meta.rendered_columns
    )]
    if any(x is None for x in shape) or shape[:2] != shape[2:]:
        return ScaleSourceReason.DICOM_PIXEL_GRID_UNATTESTED
    if not math.isclose(rowcol[0], rowcol[1], rel_tol=1e-5):
        # Existing cephalometric geometry has a scalar mm/px, so anisotropic
        # images must never be reduced to an average spacing.
        return ScaleSourceReason.DICOM_ANISOTROPIC_SPACING
    if str(meta.calibration_type or "").upper() not in {"FIDUCIAL", "GEOMETRY"}:
        return ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED
    if not isinstance(meta.calibration_description, str) or not meta.calibration_description.strip():
        return ScaleSourceReason.DICOM_DESCRIPTION_MISSING
    # Even properly sourced tags do NOT prove the correct depth/plane for each
    # cephalometric landmark. They are reviewed, not applied.
    return ScaleSourceReason.DICOM_CALIBRATION_UNATTESTED


def resolve_scale_sources(
    *,
    dicom: DicomScaleEvidence | None = None,
    ruler: CalibrationCandidate | None = None,
    server_validated_profile: ValidatedFiducialProfile | None = None,
) -> ScaleSourceResolution:
    """Choose a safe next step; NEVER mutate an analysis or DB.

    The validated profile must come from an authenticated server registry and
    its persisted server-owned binding (as checked in cephalo_auto_calibration).
    This resolver cannot certify such a binding on behalf of a client.
    """
    if ruler is None and dicom is None:
        return ScaleSourceResolution(ScaleSourceState.NO_PHYSICAL_SOURCE, ScaleSourceReason.NO_EVIDENCE, "none")

    if ruler is not None and server_validated_profile is not None:
        gate = evaluate_auto_calibration(ruler, profile=server_validated_profile)
        if gate.state is AutoCalibrationState.AUTO_VERIFIED and gate.mm_per_pixel is not None:
            if dicom is not None and _spacing(dicom.pixel_spacing) is not None:
                row, col = _spacing(dicom.pixel_spacing)
                if (not math.isclose(row, col, rel_tol=1e-5)
                    or not math.isclose(row, gate.mm_per_pixel, rel_tol=0.02)):
                    return ScaleSourceResolution(
                        ScaleSourceState.SOURCE_CONFLICT,
                        ScaleSourceReason.SOURCES_DISAGREE, "multiple",
                    )
            return ScaleSourceResolution(
                ScaleSourceState.FIDUCIAL_GATE_READY,
                ScaleSourceReason.SERVER_PROFILE_GATE_PASSED,
                "server_validated_fiducial",
                eligible_mm_per_pixel=gate.mm_per_pixel,
                profile_id=server_validated_profile.profile_id,
            )
        return ScaleSourceResolution(
            ScaleSourceState.IMAGE_RULER_UNVERIFIED,
            ScaleSourceReason.SERVER_PROFILE_GATE_FAILED, "fiducial",
        )

    if dicom is not None:
        reason = _dicom_reason(dicom)
        return ScaleSourceResolution(
            ScaleSourceState.DICOM_REVIEW_REQUIRED,
            reason, "dicom",
        )
    return ScaleSourceResolution(
        ScaleSourceState.IMAGE_RULER_UNVERIFIED,
        ScaleSourceReason.RULER_WITHOUT_PROFILE, "fiducial",
    )


def manual_calibration_required(resolution: ScaleSourceResolution) -> bool:
    """Only a ready server profile can proceed to a *separate* authenticated gate."""
    return resolution.state is not ScaleSourceState.FIDUCIAL_GATE_READY
