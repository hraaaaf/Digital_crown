"""Canonical source resolver for V1-05/F5 cephalometric superimposition.

This layer does not run image registration. It proves that both source images
come from two canonical orthodontic timepoints of the same patient/case and
applies the currently approved applicability boundary from F5-MDR-001.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import math
from typing import Optional

from sqlalchemy.orm import Session

from backend import models


ADULT_VALIDATION_MIN_AGE_YEARS = 18


class SuperimpositionSourceError(ValueError):
    """Fail-closed source-contract error with a stable machine-readable code."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ResolvedCephaloSource:
    timepoint_id: int
    timepoint_ordinal: int
    occurred_at: datetime
    cephalo_analysis_id: int
    image_original_path: str
    is_calibrated: bool
    mm_per_pixel: Optional[float]


@dataclass(frozen=True)
class ResolvedSuperimpositionPair:
    patient_id: int
    ortho_case_id: int
    from_source: ResolvedCephaloSource
    to_source: ResolvedCephaloSource
    quantitative_mm_allowed: bool
    applicability_status: str = "ADULT_ENGINEERING_SCOPE_ONLY"

    def to_metadata(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "ortho_case_id": self.ortho_case_id,
            "from_timepoint_id": self.from_source.timepoint_id,
            "to_timepoint_id": self.to_source.timepoint_id,
            "from_cephalo_analysis_id": self.from_source.cephalo_analysis_id,
            "to_cephalo_analysis_id": self.to_source.cephalo_analysis_id,
            "from_calibrated": self.from_source.is_calibrated,
            "to_calibrated": self.to_source.is_calibrated,
            "quantitative_mm_allowed": self.quantitative_mm_allowed,
            "applicability_status": self.applicability_status,
        }


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise SuperimpositionSourceError(
        "INVALID_DATE",
        "Patient birth date and timepoint dates must be valid dates.",
    )


def _age_years_at(birth_date, occurred_at) -> int:
    born = _as_date(birth_date)
    event = _as_date(occurred_at)
    if event < born:
        raise SuperimpositionSourceError(
            "INVALID_CHRONOLOGY",
            "Timepoint cannot precede patient birth date.",
        )
    return event.year - born.year - ((event.month, event.day) < (born.month, born.day))


def _validate_calibration_integrity(analysis: models.CephaloAnalysis) -> None:
    if not analysis.is_calibrated:
        return
    ratio = analysis.mm_per_pixel
    if ratio is None:
        raise SuperimpositionSourceError(
            "INVALID_CALIBRATION",
            "Calibrated cephalometric analysis is missing mm_per_pixel.",
        )
    try:
        numeric_ratio = float(ratio)
    except (TypeError, ValueError) as exc:
        raise SuperimpositionSourceError(
            "INVALID_CALIBRATION",
            "Calibrated cephalometric analysis has a non-numeric mm_per_pixel.",
        ) from exc
    if not math.isfinite(numeric_ratio) or numeric_ratio <= 0.0:
        raise SuperimpositionSourceError(
            "INVALID_CALIBRATION",
            "Calibrated cephalometric analysis has an invalid mm_per_pixel.",
        )


def _resolve_cephalo_for_timepoint(
    db: Session,
    *,
    patient_id: int,
    case_id: int,
    employer_id: int,
    timepoint: models.OrthoTimepoint,
) -> ResolvedCephaloSource:
    cephalo_evidences = (
        db.query(models.OrthoTimepointEvidence)
        .filter(
            models.OrthoTimepointEvidence.ortho_timepoint_id == timepoint.id,
            models.OrthoTimepointEvidence.patient_id == patient_id,
            models.OrthoTimepointEvidence.employer_id == employer_id,
            models.OrthoTimepointEvidence.cephalo_analysis_id.is_not(None),
        )
        .all()
    )
    if not cephalo_evidences:
        raise SuperimpositionSourceError(
            "CEPHALO_EVIDENCE_MISSING",
            f"Timepoint T{timepoint.ordinal} has no canonical CephaloAnalysis evidence.",
        )
    if len(cephalo_evidences) != 1:
        raise SuperimpositionSourceError(
            "CEPHALO_EVIDENCE_AMBIGUOUS",
            f"Timepoint T{timepoint.ordinal} has multiple CephaloAnalysis evidences; F5 will not guess.",
        )

    evidence = cephalo_evidences[0]
    analysis = (
        db.query(models.CephaloAnalysis)
        .filter(
            models.CephaloAnalysis.id == evidence.cephalo_analysis_id,
            models.CephaloAnalysis.patient_id == patient_id,
        )
        .first()
    )
    if analysis is None:
        raise SuperimpositionSourceError(
            "CEPHALO_ANALYSIS_MISSING",
            "Timepoint evidence points to a missing or cross-patient CephaloAnalysis.",
        )

    image_path = str(analysis.image_original_path or "").strip()
    if not image_path:
        raise SuperimpositionSourceError(
            "SOURCE_IMAGE_MISSING",
            "Canonical CephaloAnalysis has no original image path.",
        )

    _validate_calibration_integrity(analysis)

    return ResolvedCephaloSource(
        timepoint_id=timepoint.id,
        timepoint_ordinal=timepoint.ordinal,
        occurred_at=timepoint.occurred_at,
        cephalo_analysis_id=analysis.id,
        image_original_path=image_path,
        is_calibrated=bool(analysis.is_calibrated),
        mm_per_pixel=float(analysis.mm_per_pixel) if analysis.mm_per_pixel is not None else None,
    )


def resolve_superimposition_pair(
    db: Session,
    *,
    patient_id: int,
    case_id: int,
    employer_id: int,
    from_timepoint_id: int,
    to_timepoint_id: int,
) -> ResolvedSuperimpositionPair:
    """Resolve two canonical adult F5 sources without copying any media."""

    if from_timepoint_id == to_timepoint_id:
        raise SuperimpositionSourceError(
            "SAME_TIMEPOINT",
            "F5 requires two distinct orthodontic timepoints.",
        )

    patient = (
        db.query(models.Patient)
        .filter(
            models.Patient.id == patient_id,
            models.Patient.employer_id == employer_id,
            models.Patient.deleted_at.is_(None),
        )
        .first()
    )
    if patient is None:
        raise SuperimpositionSourceError(
            "PATIENT_NOT_FOUND",
            "Patient is missing, deleted, or outside the current cabinet.",
        )

    case = (
        db.query(models.OrthoCase)
        .filter(
            models.OrthoCase.id == case_id,
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
        )
        .first()
    )
    if case is None:
        raise SuperimpositionSourceError(
            "CASE_NOT_FOUND",
            "Orthodontic case is missing or outside the patient/cabinet scope.",
        )

    timepoints = (
        db.query(models.OrthoTimepoint)
        .filter(
            models.OrthoTimepoint.id.in_([from_timepoint_id, to_timepoint_id]),
            models.OrthoTimepoint.ortho_case_id == case_id,
            models.OrthoTimepoint.patient_id == patient_id,
            models.OrthoTimepoint.employer_id == employer_id,
        )
        .all()
    )
    by_id = {item.id: item for item in timepoints}
    from_timepoint = by_id.get(from_timepoint_id)
    to_timepoint = by_id.get(to_timepoint_id)
    if from_timepoint is None or to_timepoint is None:
        raise SuperimpositionSourceError(
            "TIMEPOINT_NOT_FOUND",
            "Both timepoints must belong to the same canonical orthodontic case.",
        )

    if from_timepoint.ordinal >= to_timepoint.ordinal or from_timepoint.occurred_at > to_timepoint.occurred_at:
        raise SuperimpositionSourceError(
            "TIMEPOINT_ORDER_INVALID",
            "F5 requires an earlier from-timepoint and a later to-timepoint.",
        )

    from_age = _age_years_at(patient.date_naissance, from_timepoint.occurred_at)
    to_age = _age_years_at(patient.date_naissance, to_timepoint.occurred_at)
    if from_age < ADULT_VALIDATION_MIN_AGE_YEARS or to_age < ADULT_VALIDATION_MIN_AGE_YEARS:
        raise SuperimpositionSourceError(
            "POPULATION_NOT_VALIDATED",
            "F5-MDR-001 is not validated for growing patients; adult-only engineering scope.",
        )

    from_source = _resolve_cephalo_for_timepoint(
        db,
        patient_id=patient_id,
        case_id=case_id,
        employer_id=employer_id,
        timepoint=from_timepoint,
    )
    to_source = _resolve_cephalo_for_timepoint(
        db,
        patient_id=patient_id,
        case_id=case_id,
        employer_id=employer_id,
        timepoint=to_timepoint,
    )

    return ResolvedSuperimpositionPair(
        patient_id=patient_id,
        ortho_case_id=case_id,
        from_source=from_source,
        to_source=to_source,
        quantitative_mm_allowed=from_source.is_calibrated and to_source.is_calibrated,
    )
