from __future__ import annotations

import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SuperimpositionPixelROI(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class OrthoSuperimpositionSourceOut(BaseModel):
    timepoint_id: int
    timepoint_ordinal: int
    occurred_at: datetime.datetime
    cephalo_analysis_id: int
    is_calibrated: bool
    mm_per_pixel: float | None = None


class OrthoSuperimpositionContextOut(BaseModel):
    patient_id: int
    ortho_case_id: int
    from_source: OrthoSuperimpositionSourceOut
    to_source: OrthoSuperimpositionSourceOut
    quantitative_mm_allowed: bool
    applicability_status: str
    method_id: str
    method_version: str
    quality_status: str
    clinically_validated: bool = False


class OrthoSuperimpositionEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_timepoint_id: int
    to_timepoint_id: int
    reference_roi: SuperimpositionPixelROI
    moving_roi: SuperimpositionPixelROI


class OrthoSuperimpositionEstimateOut(BaseModel):
    context: OrthoSuperimpositionContextOut
    registration: dict[str, Any]
