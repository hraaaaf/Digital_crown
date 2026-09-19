from __future__ import annotations

import datetime
from typing import Any, Literal

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
    applicability_status: Literal["ADULT_ENGINEERING_SCOPE_ONLY"]
    method_id: Literal["ACB_STRUCTURAL_FEATURE_SIMILARITY"]
    method_version: Literal["1"]
    quality_status: Literal["ENGINE_ESTIMATE_ONLY"]
    clinically_validated: Literal[False] = False


class OrthoSuperimpositionEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_timepoint_id: int
    to_timepoint_id: int
    reference_roi: SuperimpositionPixelROI
    moving_roi: SuperimpositionPixelROI


class SuperimpositionImageSize(BaseModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class SuperimpositionTranslation(BaseModel):
    x: float
    y: float


class OrthoSuperimpositionRegistrationOut(BaseModel):
    method_id: Literal["ACB_STRUCTURAL_FEATURE_SIMILARITY"]
    method_version: Literal["1"]
    quality_status: Literal["ENGINE_ESTIMATE_ONLY"]
    clinically_validated: Literal[False] = False
    transform_direction: Literal["moving_to_reference"]
    matrix: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    rotation_degrees: float
    uniform_scale: float = Field(gt=0)
    translation_px: SuperimpositionTranslation
    good_match_count: int = Field(ge=2)
    inlier_count: int = Field(ge=2)
    reference_roi: SuperimpositionPixelROI
    moving_roi: SuperimpositionPixelROI
    reference_size_px: SuperimpositionImageSize
    moving_size_px: SuperimpositionImageSize
    algorithm: dict[str, Any]


class OrthoSuperimpositionEstimateOut(BaseModel):
    context: OrthoSuperimpositionContextOut
    registration: OrthoSuperimpositionRegistrationOut
