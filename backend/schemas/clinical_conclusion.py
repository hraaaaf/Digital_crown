import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClinicalConclusionCreate(BaseModel):
    """A conclusion explicitly retained by a practitioner.

    `proposal_text` is optional provenance only. Supplying it never makes it authoritative;
    the authoritative text is always `conclusion_text`, submitted by the practitioner.
    """

    model_config = ConfigDict(extra="forbid")

    conclusion_text: str = Field(min_length=1, max_length=8000)
    proposal_text: Optional[str] = Field(default=None, max_length=8000)
    proposal_source: Optional[str] = Field(default=None, max_length=100)

    @field_validator("conclusion_text", mode="before")
    @classmethod
    def strip_required_conclusion(cls, value):
        cleaned = "" if value is None else str(value).strip()
        if not cleaned:
            raise ValueError("La conclusion clinique ne peut pas être vide")
        return cleaned

    @field_validator("proposal_text", "proposal_source", mode="before")
    @classmethod
    def strip_optional_provenance(cls, value):
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None


class ClinicalConclusionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    conclusion_text: str
    proposal_text: Optional[str] = None
    proposal_source: Optional[str] = None
    validated_by: int
    created_at: datetime.datetime
