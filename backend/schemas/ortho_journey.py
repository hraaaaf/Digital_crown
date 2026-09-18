import enum
import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OrthoLifecycleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INTERRUPTED = "INTERRUPTED"
    ABANDONED = "ABANDONED"
    CLOSED = "CLOSED"


class OrthoPhaseKey(str, enum.Enum):
    DIAGNOSTIC = "DIAGNOSTIC"
    PREPARATION = "PREPARATION"
    APPAREILLAGE = "APPAREILLAGE"
    ALIGNEMENT = "ALIGNEMENT"
    FINITION = "FINITION"
    CONTENTION = "CONTENTION"
    CLOTURE = "CLOTURE"


class OrthoPhaseEventType(str, enum.Enum):
    START = "START"
    ENTER_PHASE = "ENTER_PHASE"
    INTERRUPT = "INTERRUPT"
    RESUME = "RESUME"
    ABANDON = "ABANDON"
    CLOSE = "CLOSE"


class OrthoCaseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    started_at: datetime.datetime
    initial_phase_key: Optional[OrthoPhaseKey] = None


class OrthoTransitionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: OrthoPhaseEventType
    effective_at: datetime.datetime
    phase_key: Optional[OrthoPhaseKey] = None
    note: Optional[str] = None

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value):
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_phase_contract(self):
        if self.event_type == OrthoPhaseEventType.ENTER_PHASE and self.phase_key is None:
            raise ValueError("phase_key est requis pour ENTER_PHASE")
        if self.event_type != OrthoPhaseEventType.ENTER_PHASE and self.phase_key is not None:
            raise ValueError("phase_key est autorisé uniquement pour ENTER_PHASE")
        return self


class OrthoPhaseEventOut(BaseModel):
    id: int
    ortho_case_id: int
    event_type: OrthoPhaseEventType
    phase_key: Optional[OrthoPhaseKey] = None
    effective_at: datetime.datetime
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class OrthoCaseOut(BaseModel):
    id: int
    patient_id: int
    started_at: datetime.datetime
    lifecycle_status: OrthoLifecycleStatus
    current_phase_key: Optional[OrthoPhaseKey] = None
    closed_at: Optional[datetime.datetime] = None
    created_by: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    events: List[OrthoPhaseEventOut] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class OrthoControlCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    occurred_at: datetime.datetime
    phase_key: Optional[OrthoPhaseKey] = None
    appointment_id: Optional[int] = None
    note: Optional[str] = None
    next_control_at: Optional[datetime.datetime] = None

    @field_validator("note")
    @classmethod
    def normalize_control_note(cls, value):
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validate_next_control(self):
        if self.next_control_at is not None and self.next_control_at < self.occurred_at:
            raise ValueError("next_control_at ne peut pas précéder occurred_at")
        return self


class OrthoControlOut(BaseModel):
    id: int
    ortho_case_id: int
    patient_id: int
    appointment_id: Optional[int] = None
    occurred_at: datetime.datetime
    phase_key: Optional[OrthoPhaseKey] = None
    note: Optional[str] = None
    next_control_at: Optional[datetime.datetime] = None
    created_by: Optional[int] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class OrthoTimepointCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ordinal: int = Field(ge=0, le=999)
    occurred_at: datetime.datetime
    note: Optional[str] = None

    @field_validator("note")
    @classmethod
    def normalize_timepoint_note(cls, value):
        if value is None:
            return None
        value = value.strip()
        return value or None


class OrthoTimepointEvidenceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    clinical_asset_id: Optional[int] = None
    cephalo_analysis_id: Optional[int] = None
    panoramic_analysis_id: Optional[int] = None

    @model_validator(mode="after")
    def validate_exactly_one_source(self):
        count = sum(
            value is not None
            for value in (
                self.clinical_asset_id,
                self.cephalo_analysis_id,
                self.panoramic_analysis_id,
            )
        )
        if count != 1:
            raise ValueError("Une seule source canonique doit être référencée")
        return self


class OrthoTimepointEvidenceOut(BaseModel):
    id: int
    clinical_asset_id: Optional[int] = None
    cephalo_analysis_id: Optional[int] = None
    panoramic_analysis_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: datetime.datetime
    model_config = ConfigDict(from_attributes=True)


class OrthoTimepointOut(BaseModel):
    id: int
    ortho_case_id: int
    patient_id: int
    ordinal: int
    occurred_at: datetime.datetime
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime.datetime
    evidences: List[OrthoTimepointEvidenceOut] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
