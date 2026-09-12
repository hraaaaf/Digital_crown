"""R13 versioned contracts for sourced therapeutic-option evaluation.

R13 deliberately stops before a final treatment plan. Therapeutic criteria and
options are evaluable only through explicit source-locked rules, and option
selection remains a clinician action with an auditable validation record.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


R13_INDICATION_CONTRACT_VERSION = "R13_INDICATION_V1"
R13_CONTRAINDICATION_CONTRACT_VERSION = "R13_CONTRAINDICATION_V1"
R13_OPTION_CONTRACT_VERSION = "R13_TREATMENT_OPTION_V1"


class TherapeuticCriterionType(str, Enum):
    INDICATION = "INDICATION"
    CONTRAINDICATION = "CONTRAINDICATION"


class TherapeuticCriterionState(str, Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    BLOCKED = "BLOCKED"


class R13TreatmentOptionStatus(str, Enum):
    EVALUABLE = "EVALUABLE"
    BLOCKED = "BLOCKED"
    CLINICIAN_SELECTED = "CLINICIAN_SELECTED"
    CLINICIAN_REJECTED = "CLINICIAN_REJECTED"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class R13TherapeuticSourceRef(_StrictModel):
    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)


class R13TherapeuticCriterionEvidence(_StrictModel):
    """One explicit indication or contraindication evaluation."""

    criterion_id: str = Field(min_length=1)
    artifact_type: Literal["THERAPEUTIC_CRITERION"] = "THERAPEUTIC_CRITERION"
    contract_version: str = Field(min_length=1)
    criterion_type: TherapeuticCriterionType
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    source_refs: List[R13TherapeuticSourceRef] = Field(min_length=1)
    context: Dict[str, str] = Field(min_length=1)
    required_evidence_refs: List[str] = Field(min_length=1)
    missing_data_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    statement: str = Field(min_length=1)
    state: TherapeuticCriterionState = TherapeuticCriterionState.BLOCKED

    @model_validator(mode="after")
    def validate_criterion_shape(self):
        expected_version = (
            R13_INDICATION_CONTRACT_VERSION
            if self.criterion_type == TherapeuticCriterionType.INDICATION
            else R13_CONTRAINDICATION_CONTRACT_VERSION
        )
        if self.contract_version != expected_version:
            raise ValueError(
                f"{self.criterion_type.value} criterion requires contract_version {expected_version}"
            )
        for field_name in ("required_evidence_refs", "missing_data_refs", "contradictions"):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} cannot contain duplicate values")
        source_keys = [(item.source_id, item.source_version) for item in self.source_refs]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("source_refs cannot contain duplicate source/version bindings")
        if any(not key.strip() or not value.strip() for key, value in self.context.items()):
            raise ValueError("criterion context keys and values must be non-empty")
        if self.missing_data_refs or self.contradictions:
            if self.state != TherapeuticCriterionState.BLOCKED:
                raise ValueError(
                    "criterion with missing data or contradictions must remain BLOCKED"
                )
        elif self.state == TherapeuticCriterionState.BLOCKED:
            raise ValueError(
                "BLOCKED criterion requires explicit missing data or contradictions"
            )
        return self


class R13TreatmentOptionEvidence(_StrictModel):
    """Versioned treatment option with exact R12 lineage and explicit rule bindings."""

    option_id: str = Field(min_length=1)
    artifact_type: Literal["TREATMENT_OPTION"] = "TREATMENT_OPTION"
    contract_version: Literal["R13_TREATMENT_OPTION_V1"] = R13_OPTION_CONTRACT_VERSION
    rule_id: str = Field(min_length=1)
    rule_version: str = Field(min_length=1)
    source_refs: List[R13TherapeuticSourceRef] = Field(min_length=1)
    context: Dict[str, str] = Field(min_length=1)
    objective_refs: List[str] = Field(min_length=1)
    problem_refs: List[str] = Field(min_length=1)
    diagnosis_refs: List[str] = Field(min_length=1)
    finding_refs: List[str] = Field(min_length=1)
    evidence_refs: List[str] = Field(min_length=1)
    missing_data_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    indication_refs: List[str] = Field(default_factory=list)
    contraindication_refs: List[str] = Field(default_factory=list)
    blocking_gates: List[str] = Field(default_factory=list)
    label: str = Field(min_length=1)
    status: R13TreatmentOptionStatus = R13TreatmentOptionStatus.BLOCKED
    clinician_id: Optional[str] = None
    clinician_decided_at: Optional[datetime.datetime] = None
    decision_validation_ref: Optional[str] = None

    @model_validator(mode="after")
    def validate_option_shape(self):
        for field_name in (
            "objective_refs",
            "problem_refs",
            "diagnosis_refs",
            "finding_refs",
            "evidence_refs",
            "missing_data_refs",
            "contradictions",
            "indication_refs",
            "contraindication_refs",
            "blocking_gates",
        ):
            values = getattr(self, field_name)
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} cannot contain duplicate values")
        source_keys = [(item.source_id, item.source_version) for item in self.source_refs]
        if len(source_keys) != len(set(source_keys)):
            raise ValueError("source_refs cannot contain duplicate source/version bindings")
        if any(not key.strip() or not value.strip() for key, value in self.context.items()):
            raise ValueError("option context keys and values must be non-empty")
        if self.status in {
            R13TreatmentOptionStatus.CLINICIAN_SELECTED,
            R13TreatmentOptionStatus.CLINICIAN_REJECTED,
        }:
            if not self.clinician_id or not self.clinician_decided_at or not self.decision_validation_ref:
                raise ValueError("clinician option decision requires complete audit fields")
        elif self.clinician_id or self.clinician_decided_at or self.decision_validation_ref:
            raise ValueError("non-decided treatment option cannot carry clinician decision audit")
        if self.status == R13TreatmentOptionStatus.EVALUABLE and self.blocking_gates:
            raise ValueError("evaluable treatment option cannot carry blocking gates")
        if self.status == R13TreatmentOptionStatus.BLOCKED and not self.blocking_gates:
            raise ValueError("blocked treatment option requires explicit blocking gates")
        return self
