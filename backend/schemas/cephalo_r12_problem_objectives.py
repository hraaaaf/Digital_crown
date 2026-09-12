"""R12 versioned contracts for cephalometric problem lists and objectives.

These models intentionally stop before indications, contraindications, treatment
options, mechanics, appliances, or final treatment plans. They carry explicit
upstream provenance so R12 cannot hide which validated R11 findings/diagnoses a
problem or objective came from.
"""

from __future__ import annotations

from typing import List, Literal

from pydantic import Field, model_validator

from backend.schemas.cephalo_evidence import ObjectiveEvidence, ProblemEvidence, ReviewState


R12_PROBLEM_CONTRACT_VERSION = "R12_PROBLEM_LIST_V1"
R12_OBJECTIVE_CONTRACT_VERSION = "R12_OBJECTIVE_V1"


def _require_unique(refs: List[str], *, field: str) -> None:
    if len(refs) != len(set(refs)):
        raise ValueError(f"{field} cannot contain duplicate refs")


class R12ProblemListItem(ProblemEvidence):
    """Problem-list item with direct, versioned R11 provenance."""

    artifact_type: Literal["PROBLEM_LIST_ITEM"] = "PROBLEM_LIST_ITEM"
    contract_version: Literal["R12_PROBLEM_LIST_V1"] = R12_PROBLEM_CONTRACT_VERSION
    finding_refs: List[str] = Field(min_length=1)
    missing_data_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_r12_problem_shape(self):
        _require_unique(self.diagnosis_refs, field="diagnosis_refs")
        _require_unique(self.finding_refs, field="finding_refs")
        _require_unique(self.evidence_refs, field="evidence_refs")
        _require_unique(self.missing_data_refs, field="missing_data_refs")
        if self.state == ReviewState.INSUFFICIENT_DATA and not self.missing_data_refs:
            raise ValueError(
                "R12 insufficient-data problem requires explicit missing_data_refs"
            )
        return self


class R12ObjectiveEvidence(ObjectiveEvidence):
    """Objective with direct provenance through validated R12 problems to R11."""

    artifact_type: Literal["OBJECTIVE"] = "OBJECTIVE"
    contract_version: Literal["R12_OBJECTIVE_V1"] = R12_OBJECTIVE_CONTRACT_VERSION
    diagnosis_refs: List[str] = Field(min_length=1)
    finding_refs: List[str] = Field(min_length=1)
    evidence_refs: List[str] = Field(min_length=1)
    missing_data_refs: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_r12_objective_shape(self):
        _require_unique(self.problem_refs, field="problem_refs")
        _require_unique(self.diagnosis_refs, field="diagnosis_refs")
        _require_unique(self.finding_refs, field="finding_refs")
        _require_unique(self.evidence_refs, field="evidence_refs")
        _require_unique(self.missing_data_refs, field="missing_data_refs")
        if self.state == ReviewState.INSUFFICIENT_DATA and not self.missing_data_refs:
            raise ValueError(
                "R12 insufficient-data objective requires explicit missing_data_refs"
            )
        return self
