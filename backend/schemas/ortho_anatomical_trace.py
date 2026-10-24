"""G5 LAB anatomical contour wire contract. Never accepts author/approval identity."""
from pydantic import BaseModel, ConfigDict, Field
from typing import Any


class AnatomicalContourDraftWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(gt=0)
    expected_draft_version: int = Field(ge=0)
    contours: list[dict[str, Any]] = Field(min_length=6,max_length=6)


class AnatomicalContourApproval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(gt=0)
    expected_draft_version: int = Field(gt=0)
    confirmation: str = Field(pattern=r"^JE_VALIDE_LE_TRACE_ANATOMIQUE$",max_length=35)
