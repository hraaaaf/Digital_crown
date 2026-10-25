"""Explicit patient-study-revision bound ODF note commands (no R14 promotion)."""
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class OrthoPractitionerDraftWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(strict=True,gt=0)
    expected_draft_version: int = Field(strict=True,ge=0)
    moulages: dict[str, Any] = Field(default_factory=dict)
    resume_diagnostique: str = Field(default="",max_length=10000)
    plan_traitement: str = Field(default="",max_length=10000)


class OrthoPractitionerDraftApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(strict=True,gt=0)
    expected_draft_version: int = Field(strict=True,gt=0)
    confirmation: str = Field(pattern=r"^JE_CONFIRME_MES_NOTES$")
