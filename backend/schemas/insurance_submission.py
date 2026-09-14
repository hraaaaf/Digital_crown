from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InsuranceOrganization(str, Enum):
    CNSS = "CNSS"
    CNOPS = "CNOPS"
    FAR = "FAR"


class InsuranceMappingStatus(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    EXACT = "EXACT"
    AMBIGUOUS = "AMBIGUOUS"
    NO_MATCH = "NO_MATCH"
    OUTDATED = "OUTDATED"


class InsuranceDraftStatus(str, Enum):
    INCOMPLETE = "INCOMPLETE"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    VALIDATED = "VALIDATED"


class InsuranceLineSource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    honoraires_document_id: int
    honoraires_line_index: int = Field(ge=0)
    acte_id: Optional[int] = None
    source_line_uid: Optional[str] = None
    catalog_act_id: Optional[int] = None


class InsuranceSubmissionLine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: InsuranceLineSource
    service_date: date
    label: str = Field(min_length=1)
    teeth: List[str] = Field(default_factory=list)
    amount_mad: float = Field(gt=0, le=1_000_000)
    mapping_status: InsuranceMappingStatus = InsuranceMappingStatus.NOT_EVALUATED
    ngap_code: Optional[str] = None
    ngap_coefficient: Optional[float] = Field(default=None, gt=0)
    mapping_rule_id: Optional[str] = None

    @model_validator(mode="after")
    def enforce_exact_mapping_traceability(self):
        if self.mapping_status == InsuranceMappingStatus.EXACT:
            if not self.ngap_code or not self.ngap_code.strip():
                raise ValueError("EXACT mapping requires ngap_code")
            if not self.mapping_rule_id or not self.mapping_rule_id.strip():
                raise ValueError("EXACT mapping requires mapping_rule_id")
        elif self.ngap_code:
            raise ValueError("ngap_code is allowed only for EXACT mapping")
        return self


class InsuranceTemplateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    template_version: str = Field(min_length=1)
    template_hash: Optional[str] = None
    source_url: Optional[str] = None


class InsuranceReferenceSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ngap_reference_version: Optional[str] = None
    ngap_reference_hash: Optional[str] = None


class InsuranceSubmissionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1"
    patient_id: int
    organization: InsuranceOrganization
    honoraires_document_id: int
    lines: List[InsuranceSubmissionLine] = Field(min_length=1)
    unresolved_fields: List[str] = Field(default_factory=list)
    status: InsuranceDraftStatus = InsuranceDraftStatus.INCOMPLETE
    template: InsuranceTemplateSnapshot
    reference: InsuranceReferenceSnapshot = Field(default_factory=InsuranceReferenceSnapshot)
    source_ordonnance_document_id: Optional[int] = None
    validated_by_practitioner_id: Optional[int] = None
    validated_at: Optional[datetime] = None

    @model_validator(mode="after")
    def enforce_validation_state(self):
        all_mappings_exact = all(line.mapping_status == InsuranceMappingStatus.EXACT for line in self.lines)
        if self.status == InsuranceDraftStatus.READY_FOR_REVIEW:
            if self.unresolved_fields or not all_mappings_exact:
                raise ValueError("READY_FOR_REVIEW requires no unresolved fields and EXACT mappings")
        if self.status == InsuranceDraftStatus.VALIDATED:
            if self.unresolved_fields or not all_mappings_exact:
                raise ValueError("VALIDATED requires no unresolved fields and EXACT mappings")
            if self.validated_by_practitioner_id is None or self.validated_at is None:
                raise ValueError("VALIDATED requires practitioner id and validation timestamp")
        return self
