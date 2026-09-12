"""R14 versioned contract for final clinical validation.

R14 consumes only R13 therapeutic objects. It may represent a blocked or
awaiting-validation clinical strategy, but no state is final until a clinician
validation record is present and validated by the R14 safety layer.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.cephalo_r13_therapeutic_options import R13TherapeuticSourceRef


R14_FINAL_VALIDATION_CONTRACT_VERSION = "R14_FINAL_CLINICAL_VALIDATION_V1"


class R14FinalClinicalStatus(str, Enum):
    BLOCKED = "BLOCKED"
    AWAITING_CLINICIAN_VALIDATION = "AWAITING_CLINICIAN_VALIDATION"
    CLINICIAN_VALIDATED = "CLINICIAN_VALIDATED"
    CLINICIAN_REJECTED = "CLINICIAN_REJECTED"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class R14FinalClinicalStrategyEvidence(_StrictModel):
    """Traceable final-clinical strategy boundary, never autonomous treatment planning."""

    strategy_id: str = Field(min_length=1)
    artifact_type: Literal["FINAL_CLINICAL_STRATEGY"] = "FINAL_CLINICAL_STRATEGY"
    contract_version: Literal["R14_FINAL_CLINICAL_VALIDATION_V1"] = (
        R14_FINAL_VALIDATION_CONTRACT_VERSION
    )
    option_refs: List[str] = Field(min_length=1)
    option_validation_refs: List[str] = Field(default_factory=list)
    criterion_refs: List[str] = Field(default_factory=list)
    source_refs: List[R13TherapeuticSourceRef] = Field(min_length=1)
    objective_refs: List[str] = Field(min_length=1)
    problem_refs: List[str] = Field(min_length=1)
    diagnosis_refs: List[str] = Field(min_length=1)
    finding_refs: List[str] = Field(min_length=1)
    evidence_refs: List[str] = Field(min_length=1)
    missing_data_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    blocking_gates: List[str] = Field(default_factory=list)
    status: R14FinalClinicalStatus = R14FinalClinicalStatus.BLOCKED
    clinician_id: Optional[str] = None
    clinician_validated_at: Optional[datetime.datetime] = None
    final_validation_ref: Optional[str] = None

    @model_validator(mode="after")
    def validate_strategy_shape(self):
        for field_name in (
            "option_refs",
            "option_validation_refs",
            "criterion_refs",
            "objective_refs",
            "problem_refs",
            "diagnosis_refs",
            "finding_refs",
            "evidence_refs",
            "missing_data_refs",
            "contradictions",
            "blocking_gates",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} cannot contain duplicate values")

        source_keys = [(item.source_id, item.source_version) for item in self.source_refs]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("source_refs cannot contain duplicate source/version bindings")

        final_states = {
            R14FinalClinicalStatus.CLINICIAN_VALIDATED,
            R14FinalClinicalStatus.CLINICIAN_REJECTED,
        }
        if self.status in final_states:
            if self.blocking_gates:
                raise ValueError("final R14 clinical state cannot carry blocking gates")
            if not self.clinician_id or not self.clinician_validated_at or not self.final_validation_ref:
                raise ValueError("final R14 clinical state requires complete clinician validation audit")
            if (
                self.clinician_validated_at.tzinfo is None
                or self.clinician_validated_at.utcoffset() is None
            ):
                raise ValueError("clinician_validated_at must be timezone-aware")
        else:
            if self.clinician_id or self.clinician_validated_at or self.final_validation_ref:
                raise ValueError("non-final R14 strategy cannot carry final clinician validation audit")

        if self.status == R14FinalClinicalStatus.BLOCKED and not self.blocking_gates:
            raise ValueError("blocked R14 strategy requires explicit blocking gates")
        if (
            self.status == R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION
            and self.blocking_gates
        ):
            raise ValueError("awaiting-clinician-validation strategy cannot carry blocking gates")
        return self
