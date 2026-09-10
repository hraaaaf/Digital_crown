"""Typed evidence graph for cephalometric diagnosis and treatment planning.

These schemas are intentionally independent from the current legacy/free-text
cephalo payload. They establish the future source-of-truth contract without
activating any normative rule, diagnosis or treatment recommendation.
"""

from __future__ import annotations

import datetime
import math
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceStatus(str, Enum):
    OBSERVED = "OBSERVED"
    COMPUTED = "COMPUTED"
    INTERPRETED = "INTERPRETED"
    CLINICIAN_VALIDATED = "CLINICIAN_VALIDATED"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_COMPUTABLE = "NOT_COMPUTABLE"


class LandmarkOrigin(str, Enum):
    SRPOSE38_AUTO = "SRPOSE38_AUTO"
    MANUAL = "MANUAL"
    MANUAL_CORRECTED = "MANUAL_CORRECTED"


class ReviewState(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    EDITED = "EDITED"
    REJECTED = "REJECTED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class TreatmentOptionStatus(str, Enum):
    EVALUABLE = "EVALUABLE"
    BLOCKED_INSUFFICIENT_DATA = "BLOCKED_INSUFFICIENT_DATA"
    REJECTED = "REJECTED"
    CLINICIAN_SELECTED = "CLINICIAN_SELECTED"


class ValidationAction(str, Enum):
    ACCEPT = "ACCEPT"
    EDIT = "EDIT"
    REJECT = "REJECT"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceEvidence(_StrictModel):
    evidence_id: str = Field(min_length=1)
    patient_id: int
    kind: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    acquired_at: Optional[datetime.datetime] = None
    recorded_at: datetime.datetime
    operator_id: Optional[str] = None
    evidence_status: EvidenceStatus = EvidenceStatus.OBSERVED
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    quality_status: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LandmarkEvidence(_StrictModel):
    evidence_id: str = Field(min_length=1)
    landmark_id: str = Field(min_length=1)
    x: float
    y: float
    source_image_ref: str = Field(min_length=1)
    origin: LandmarkOrigin
    model_id: Optional[str] = None
    model_sha256: Optional[str] = None
    pipeline_version: Optional[str] = None
    original_auto_x: Optional[float] = None
    original_auto_y: Optional[float] = None
    validated_by: Optional[str] = None
    validated_at: Optional[datetime.datetime] = None
    evidence_refs: List[str] = Field(min_length=1)
    evidence_status: EvidenceStatus
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE

    @model_validator(mode="after")
    def validate_origin_contract(self):
        if not math.isfinite(self.x) or not math.isfinite(self.y):
            raise ValueError("Landmark coordinates must be finite")
        for original in (self.original_auto_x, self.original_auto_y):
            if original is not None and not math.isfinite(original):
                raise ValueError("Original automatic coordinates must be finite")
        if self.origin == LandmarkOrigin.SRPOSE38_AUTO:
            if not self.model_id or not self.model_sha256 or not self.pipeline_version:
                raise ValueError("Automatic landmark requires model id, SHA256 and pipeline version")
        if self.origin == LandmarkOrigin.MANUAL_CORRECTED:
            if self.original_auto_x is None or self.original_auto_y is None:
                raise ValueError("Manual correction must preserve original automatic coordinates")
            if not self.validated_by or not self.validated_at:
                raise ValueError("Manual correction requires clinician/operator audit")
        return self


class ConstructionEvidence(_StrictModel):
    construction_id: str = Field(min_length=1)
    definition_id: str = Field(min_length=1)
    definition_version: str = Field(min_length=1)
    landmark_refs: List[str] = Field(min_length=1)
    geometry: Dict[str, Any]
    evidence_refs: List[str] = Field(min_length=1)
    evidence_status: EvidenceStatus = EvidenceStatus.COMPUTED
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class MeasurementEvidence(_StrictModel):
    measurement_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    method_version: str = Field(min_length=1)
    value: Optional[float] = None
    unit: str = Field(min_length=1)
    landmark_refs: List[str] = Field(default_factory=list)
    construction_refs: List[str] = Field(default_factory=list)
    calibration_ref: Optional[str] = None
    requires_calibration: bool = False
    evidence_refs: List[str] = Field(min_length=1)
    evidence_status: EvidenceStatus = EvidenceStatus.COMPUTED
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE

    @model_validator(mode="after")
    def validate_measurement_contract(self):
        if not self.landmark_refs and not self.construction_refs:
            raise ValueError("Measurement requires landmark or construction dependencies")
        if self.requires_calibration and not self.calibration_ref:
            raise ValueError("Calibrated linear measurement requires calibration_ref")
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError("Measurement value must be finite")
        if self.availability_status != AvailabilityStatus.AVAILABLE and self.value is not None:
            raise ValueError("Unavailable measurement cannot carry a patient value")
        if self.availability_status == AvailabilityStatus.AVAILABLE and self.value is None:
            raise ValueError("Available measurement requires a patient value")
        return self


class NormativeEvaluationEvidence(_StrictModel):
    evaluation_id: str = Field(min_length=1)
    measurement_ref: str = Field(min_length=1)
    norm_profile_id: str = Field(min_length=1)
    norm_profile_version: str = Field(min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    reference: Dict[str, Any]
    classification_rule_id: Optional[str] = None
    classification: Optional[str] = None
    source_refs: List[str] = Field(min_length=1)
    evidence_refs: List[str] = Field(min_length=1)
    evidence_status: EvidenceStatus = EvidenceStatus.INTERPRETED
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE

    @model_validator(mode="after")
    def validate_normative_contract(self):
        if self.availability_status == AvailabilityStatus.AVAILABLE and not self.reference:
            raise ValueError("Available normative evaluation requires an explicit reference")
        if self.classification is not None and not self.classification_rule_id:
            raise ValueError("Normative classification requires a versioned classification rule")
        return self


class FindingEvidence(_StrictModel):
    finding_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    supporting_evidence_refs: List[str] = Field(min_length=1)
    opposing_evidence_refs: List[str] = Field(default_factory=list)
    missing_evidence_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    statement: str = Field(min_length=1)
    evidence_status: EvidenceStatus = EvidenceStatus.INTERPRETED
    availability_status: AvailabilityStatus = AvailabilityStatus.AVAILABLE


class DiagnosticHypothesisEvidence(_StrictModel):
    diagnosis_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)
    supporting_finding_refs: List[str] = Field(min_length=1)
    opposing_finding_refs: List[str] = Field(default_factory=list)
    missing_data_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    statement: str = Field(min_length=1)
    state: ReviewState = ReviewState.PROPOSED
    clinician_id: Optional[str] = None
    clinician_validated_at: Optional[datetime.datetime] = None

    @model_validator(mode="after")
    def accepted_diagnosis_requires_clinician(self):
        if self.state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
            if not self.clinician_id or not self.clinician_validated_at:
                raise ValueError("Accepted/edited diagnosis requires clinician validation")
        return self


class ProblemEvidence(_StrictModel):
    problem_id: str = Field(min_length=1)
    diagnosis_refs: List[str] = Field(min_length=1)
    evidence_refs: List[str] = Field(min_length=1)
    statement: str = Field(min_length=1)
    priority: Optional[int] = Field(default=None, ge=1)
    state: ReviewState = ReviewState.PROPOSED
    clinician_id: Optional[str] = None
    clinician_validated_at: Optional[datetime.datetime] = None

    @model_validator(mode="after")
    def accepted_problem_requires_clinician(self):
        if self.state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
            if not self.clinician_id or not self.clinician_validated_at:
                raise ValueError("Accepted/edited problem requires clinician validation")
        return self


class ObjectiveEvidence(_StrictModel):
    objective_id: str = Field(min_length=1)
    problem_refs: List[str] = Field(min_length=1)
    target: str = Field(min_length=1)
    success_criterion: str = Field(min_length=1)
    state: ReviewState = ReviewState.PROPOSED
    clinician_id: Optional[str] = None
    clinician_validated_at: Optional[datetime.datetime] = None

    @model_validator(mode="after")
    def accepted_objective_requires_clinician(self):
        if self.state in {ReviewState.ACCEPTED, ReviewState.EDITED}:
            if not self.clinician_id or not self.clinician_validated_at:
                raise ValueError("Accepted/edited objective requires clinician validation")
        return self


class TreatmentOptionEvidence(_StrictModel):
    option_id: str = Field(min_length=1)
    objective_refs: List[str] = Field(min_length=1)
    required_evidence_refs: List[str] = Field(min_length=1)
    missing_gates: List[str] = Field(default_factory=list)
    indication_refs: List[str] = Field(default_factory=list)
    contraindication_refs: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    limits: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    growth_dependency: Optional[str] = None
    anchorage_requirements: List[str] = Field(default_factory=list)
    profile_considerations: List[str] = Field(default_factory=list)
    stability_considerations: List[str] = Field(default_factory=list)
    status: TreatmentOptionStatus = TreatmentOptionStatus.EVALUABLE
    clinician_id: Optional[str] = None
    clinician_selected_at: Optional[datetime.datetime] = None

    @model_validator(mode="after")
    def validate_option_contract(self):
        if self.missing_gates and self.status in {
            TreatmentOptionStatus.EVALUABLE,
            TreatmentOptionStatus.CLINICIAN_SELECTED,
        }:
            raise ValueError("Treatment option with missing gates cannot be evaluable or selected")
        if self.status == TreatmentOptionStatus.CLINICIAN_SELECTED:
            if not self.clinician_id or not self.clinician_selected_at:
                raise ValueError("Clinician-selected treatment option requires clinician audit")
        return self


class ClinicianValidationEvidence(_StrictModel):
    validation_id: str = Field(min_length=1)
    clinician_id: str = Field(min_length=1)
    validated_at: datetime.datetime
    action: ValidationAction
    target_type: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    before_snapshot_hash: str = Field(min_length=1)
    after_snapshot_hash: str = Field(min_length=1)
    reason: Optional[str] = None


class TreatmentPhaseEvidence(_StrictModel):
    phase_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    objective_refs: List[str] = Field(min_length=1)
    mechanics_or_appliances: List[str] = Field(default_factory=list)
    procedures: List[str] = Field(default_factory=list)
    monitoring: List[str] = Field(default_factory=list)
    reassessment_criteria: List[str] = Field(default_factory=list)


class FinalPlanEvidence(_StrictModel):
    plan_id: str = Field(min_length=1)
    selected_option_ref: str = Field(min_length=1)
    validated_diagnosis_refs: List[str] = Field(min_length=1)
    validated_problem_refs: List[str] = Field(min_length=1)
    validated_objective_refs: List[str] = Field(min_length=1)
    phases: List[TreatmentPhaseEvidence] = Field(min_length=1)
    retention: List[str] = Field(default_factory=list)
    reassessment_points: List[str] = Field(default_factory=list)
    clinician_id: str = Field(min_length=1)
    clinician_validated_at: datetime.datetime
    validation_ref: str = Field(min_length=1)
