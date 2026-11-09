"""CEPH-PREMIUM-V1 / J2.1-M1: isolated canonical *draft* scene contract.

This is an intentionally NONCLINICAL, immutable-in-memory data contract.
It creates no database rows, file writes, HTTP routes, ONNX calls, clinical
conclusions, trusted media-source associations or PDF archives.

The validated declared SHA hashes do not prove their corresponding source
bytes have been verified; callers must perform DC-DOS-05 authenticated reads.
A legacy SRPose38 index→anatomic-name mapping is NOT source-certified.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.services.srpose38_contract import (
    SOTA_LANDMARKS_MAPPING, SRPOSE38_MODEL_NAME, SRPOSE38_MODEL_SHA256,
)

SCENE_VERSION = "CEPH_PREMIUM_SCENE_V1_DRAFT"
_SHA = re.compile(r"^[0-9a-f]{64}$")
_LOCAL_DETECTOR_POINTS = frozenset(SOTA_LANDMARKS_MAPPING.values())
_CONSTRUCTED_ONLY_POINTS = frozenset({"Occ_Ant", "Occ_Post"})
_CONTOURS = frozenset({
    "cranial_base", "maxilla", "mandible", "upper_incisor",
    "lower_incisor", "soft_tissue_profile",
})


def _check_digest(value: str | None, *, label: str, required: bool = True):
    if value is None and not required:
        return value
    if type(value) is not str or not _SHA.fullmatch(value):
        raise ValueError(f"{label}: expected lowercase SHA256 of 64 hex chars")
    return value


class _StrictDraftModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SceneIdentity(_StrictDraftModel):
    employer_id: int = Field(strict=True, gt=0)
    patient_id: int = Field(strict=True, gt=0)
    study_id: int = Field(strict=True, gt=0)
    original_asset_id: int = Field(strict=True, gt=0)
    original_sha256: str
    scientific_revision: int = Field(strict=True, gt=0)
    scientific_digest: str
    scene_revision: int = Field(strict=True, gt=0)
    parent_scene_sha256: str | None = None

    original_width: int = Field(strict=True, ge=64, le=20000)
    original_height: int = Field(strict=True, ge=64, le=20000)
    coordinate_system: Literal["SOURCE_IMAGE_PIXELS_TOP_LEFT"] = (
        "SOURCE_IMAGE_PIXELS_TOP_LEFT"
    )
    detector_model: Literal["srpose38-tta-1024.onnx"] = SRPOSE38_MODEL_NAME
    detector_sha256: str = SRPOSE38_MODEL_SHA256
    detector_mapping_authority: Literal["LEGACY_LOCAL_UNVERIFIED"] = (
        "LEGACY_LOCAL_UNVERIFIED"
    )

    @model_validator(mode="after")
    def validate_identity(self):
        for field in ("original_sha256", "scientific_digest", "detector_sha256"):
            _check_digest(getattr(self, field), label=field)
        _check_digest(
            self.parent_scene_sha256,
            label="parent_scene_sha256",
            required=self.scene_revision > 1,
        )
        if self.scene_revision == 1 and self.parent_scene_sha256 is not None:
            raise ValueError("Initial revision cannot claim a parent")
        if self.detector_sha256 != SRPOSE38_MODEL_SHA256:
            raise ValueError("Detector SHA does not match pinned SRPose38 contract")
        return self


class ScenePixel(_StrictDraftModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)

    @model_validator(mode="after")
    def finite(self):
        if not (math.isfinite(self.x) and math.isfinite(self.y)):
            raise ValueError("Pixel coordinates must be finite")
        return self


class SceneLandmark(ScenePixel):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
    origin: Literal["SRPOSE38_AUTO", "PRACTITIONER_EDIT", "CONSTRUCTED"]
    confidence: float | None = Field(default=None, ge=0, le=1)
    score_status: Literal["NOT_EMITTED", "AVAILABLE"] = "NOT_EMITTED"

    @model_validator(mode="after")
    def validate_landmark(self):
        if self.origin == "SRPOSE38_AUTO":
            if self.id not in _LOCAL_DETECTOR_POINTS:
                raise ValueError("ONNX channel names limited to legacy SRPose38 local contract")
            if self.score_status == "AVAILABLE":
                if self.confidence is None or not math.isfinite(self.confidence):
                    raise ValueError("Available model score must be finite and genuine")
            elif self.confidence is not None:
                raise ValueError("Score NOT_EMITTED cannot invent a confidence value")
        elif self.confidence is not None or self.score_status != "NOT_EMITTED":
            raise ValueError("Only an ONNX output can carry ONNX confidence")
        if self.origin == "CONSTRUCTED" and self.id not in _CONSTRUCTED_ONLY_POINTS:
            raise ValueError("Constructed points must use explicit construction IDs")
        if self.origin != "CONSTRUCTED" and self.id in _CONSTRUCTED_ONLY_POINTS:
            raise ValueError("Occlusal constructions are not detector landmarks")
        if self.id not in _LOCAL_DETECTOR_POINTS | _CONSTRUCTED_ONLY_POINTS:
            raise ValueError("Unsupported landmark ID in draft scene")
        return self


class SceneCalibration(_StrictDraftModel):
    status: Literal["UNVERIFIED", "CANDIDATE"] = "UNVERIFIED"
    mm_per_pixel_candidate: float | None = Field(default=None, gt=0)
    evidence_sha256: str | None = None

    @model_validator(mode="after")
    def no_authority(self):
        _check_digest(self.evidence_sha256, label="calibration evidence", required=False)
        if self.status == "UNVERIFIED":
            if self.mm_per_pixel_candidate is not None or self.evidence_sha256 is not None:
                raise ValueError("Unverified calibration cannot carry a ratio")
        else:
            if (self.mm_per_pixel_candidate is None
                or not math.isfinite(self.mm_per_pixel_candidate)
                or self.evidence_sha256 is None):
                raise ValueError("Candidate calibration requires a finite ratio and evidence")
        return self


class SceneContour(_StrictDraftModel):
    id: Literal[
        "cranial_base", "maxilla", "mandible", "upper_incisor",
        "lower_incisor", "soft_tissue_profile",
    ]
    status: Literal["AUTO_PROPOSED", "MANUAL_DRAFT"]
    points: tuple[ScenePixel, ...] = Field(strict=False, min_length=2, max_length=600)
    proposal_model_id: str | None = Field(default=None, min_length=1, max_length=120)
    proposal_model_sha256: str | None = None

    @model_validator(mode="after")
    def provenance(self):
        _check_digest(
            self.proposal_model_sha256,
            label="proposal model SHA",
            required=self.status == "AUTO_PROPOSED",
        )
        if self.status == "AUTO_PROPOSED" and not self.proposal_model_id:
            raise ValueError("Automatic contour requires independent model identity")
        if self.status == "MANUAL_DRAFT" and (
            self.proposal_model_id is not None or self.proposal_model_sha256 is not None
        ):
            raise ValueError("Unreviewed manual draft cannot claim automatic provenance")
        return self


class SceneConstruction(_StrictDraftModel):
    id: str = Field(min_length=1, max_length=80)
    kind: Literal["LINE", "ANGLE"]
    point_ids: tuple[str, ...] = Field(strict=False, min_length=2, max_length=3)

    @model_validator(mode="after")
    def geometry(self):
        if len(set(self.point_ids)) != len(self.point_ids):
            raise ValueError("Repeated reference points invalidate geometry")
        if len(self.point_ids) != (2 if self.kind == "LINE" else 3):
            raise ValueError("Construction point count incompatible with kind")
        return self


class SceneMeasurement(_StrictDraftModel):
    id: str = Field(min_length=1, max_length=80)
    unit: Literal["DEG", "MM", "PX"]
    status: Literal["RAW_NONCLINICAL", "UNAVAILABLE"]
    value: float | None = None

    @model_validator(mode="after")
    def explicit_availability(self):
        if self.status == "UNAVAILABLE":
            if self.value is not None:
                raise ValueError("Unavailable measurements must use null, never zero")
        elif self.value is None or not math.isfinite(self.value):
            raise ValueError("Numeric value required for raw nonclinical measurement")
        return self


class CephaloPremiumSceneDraft(_StrictDraftModel):
    schema_version: Literal["CEPH_PREMIUM_SCENE_V1_DRAFT"] = SCENE_VERSION
    identity: SceneIdentity
    calibration: SceneCalibration = Field(default_factory=SceneCalibration)
    landmarks: tuple[SceneLandmark, ...] = Field(default=(), strict=False)
    contours: tuple[SceneContour, ...] = Field(default=(), strict=False)
    constructions: tuple[SceneConstruction, ...] = Field(default=(), strict=False)
    measurements: tuple[SceneMeasurement, ...] = Field(default=(), strict=False)
    document_status: Literal["NONCLINICAL_DRAFT"] = "NONCLINICAL_DRAFT"
    clinical_release: Literal[False] = False

    @model_validator(mode="after")
    def validate_scene(self):
        w, h = self.identity.original_width, self.identity.original_height
        for label, collection in (
            ("landmark", self.landmarks), ("contour", self.contours),
            ("construction", self.constructions), ("measurement", self.measurements),
        ):
            ids = [item.id for item in collection]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Duplicate {label} IDs in canonical scene")
        for landmark in self.landmarks:
            if landmark.x >= w or landmark.y >= h:
                raise ValueError("Landmark outside original source pixel bounds")
        for contour in self.contours:
            for point in contour.points:
                if point.x >= w or point.y >= h:
                    raise ValueError("Contour outside original source pixel bounds")
        available = {landmark.id for landmark in self.landmarks}
        for construction in self.constructions:
            if not set(construction.point_ids) <= available:
                raise ValueError("Construction references missing landmark")
        for measurement in self.measurements:
            if measurement.unit == "MM" and measurement.status != "UNAVAILABLE":
                raise ValueError("J2.1-M1 cannot authorize numerical millimeter measurements")
        return self

    def canonical_dict(self) -> dict:
        """Stable keys and set order; never mutates scene or authorizes clinical use."""
        data = self.model_dump(mode="json", exclude_none=False)
        for field in ("landmarks", "contours", "constructions", "measurements"):
            data[field].sort(key=lambda entry: entry["id"])
        return data

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.canonical_dict(), sort_keys=True, ensure_ascii=False,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")

    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()
