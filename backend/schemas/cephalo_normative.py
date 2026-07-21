"""
Schemas + types for the cephalometric normative registry.

Phase 1 (scaffolding) built these models empty. Phase 2 (legacy inventory)
added the `origin` field so every migrated literal is traceable back to its
exact file/symbol/line in the current codebase, and `bounds_id` so
PlausibilityBounds can hold more than one origin per measurement (the same
hard/soft bound often appears in more than one file). No lookup/matching/
gating logic lives here — see backend/services/cephalo_normative_registry.py
for the loader, and the architecture design docs for the Phase 3 runtime
service that will read these types.

Nothing here is imported by any existing consumer (cephalo_engine.py,
cephalo_consistency_validator.py, ai_advisor.py, bilan_ortho_engine.py, or
any frontend file) as of Phase 2. Every entry migrated in Phase 2 is
`LEGACY_UNVALIDATED` or `QUARANTINED` — never `VALIDATED_FOR_PROFILE` — and
no value was corrected, rounded, or arbitrated between conflicting sources.
"""
from datetime import date
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


# --- ORIGIN (traceability) ---

class CodeOrigin(BaseModel):
    """Exact code location a migrated literal was copied from. `line` is a
    string (not int) to allow "156,165" when one value appears at more than
    one line in the same file (e.g. the same MetricInput repeated across two
    analysis-family tabs).
    """
    model_config = ConfigDict(extra="forbid")

    file: str
    symbol: str
    line: str


# --- STATUTS ---

class DefinitionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    QUARANTINED = "QUARANTINED"
    DEPRECATED = "DEPRECATED"


class ValidationStatus(str, Enum):
    LEGACY_UNVALIDATED = "LEGACY_UNVALIDATED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VALIDATED_FOR_PROFILE = "VALIDATED_FOR_PROFILE"
    QUARANTINED = "QUARANTINED"
    DEPRECATED = "DEPRECATED"


class ReferenceType(str, Enum):
    MEAN_SD = "MEAN_SD"
    FIXED_RANGE = "FIXED_RANGE"
    SINGLE_REFERENCE_VALUE = "SINGLE_REFERENCE_VALUE"
    CATEGORICAL_THRESHOLDS = "CATEGORICAL_THRESHOLDS"


class AgeDependencyType(str, Enum):
    AGE_INDEPENDENT = "AGE_INDEPENDENT"
    TWO_BUCKET = "TWO_BUCKET"
    CONTINUOUS_TABLE = "CONTINUOUS_TABLE"


class Sex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    POOLED = "POOLED"


# --- MEASUREMENT DEFINITION ---

class MeasurementDefinition(BaseModel):
    """What a measurement is, geometrically — landmarks, unit, formula version.

    Never carries a normative value. See NormativeProfile for that.
    """
    model_config = ConfigDict(extra="forbid")

    measurement_id: str
    canonical_name: str
    display_name: str
    analysis_family: str
    unit: str
    definition_version: str
    required_landmarks: List[str] = Field(min_length=1)
    definition_status: DefinitionStatus
    origin: CodeOrigin
    notes: Optional[str] = None


# --- NORMATIVE PROFILE ---

class NormativeProfile(BaseModel):
    """A population norm for one measurement, pinned to one exact
    measurement_definition_version. Never itself a clinical classification
    rule — see ClassificationRule for that (kept a separate artifact per the
    locked architecture decision that a reference statistic and its clinical
    cutoff are distinct, independently-sourced claims).
    """
    model_config = ConfigDict(extra="forbid")

    profile_id: str
    measurement_id: str
    measurement_definition_version: str
    reference_type: ReferenceType
    unit: str

    mean: Optional[float] = None
    sd: Optional[float] = None
    range: Optional[Tuple[float, float]] = None
    single_value: Optional[float] = None
    categorical_thresholds: Optional[List[str]] = None

    age_min: Optional[float] = None
    age_max: Optional[float] = None
    age_dependency_type: AgeDependencyType
    sex: Sex
    population_id: str

    source_id: Optional[str] = None
    validation_status: ValidationStatus
    profile_version: str
    effective_from: date
    effective_to: Optional[date] = None
    origin: CodeOrigin
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _reference_type_matches_populated_fields(self) -> "NormativeProfile":
        if self.reference_type == ReferenceType.MEAN_SD and (self.mean is None or self.sd is None):
            raise ValueError("reference_type MEAN_SD requires both mean and sd")
        if self.reference_type == ReferenceType.FIXED_RANGE and self.range is None:
            raise ValueError("reference_type FIXED_RANGE requires range")
        if self.reference_type == ReferenceType.SINGLE_REFERENCE_VALUE and self.single_value is None:
            raise ValueError("reference_type SINGLE_REFERENCE_VALUE requires single_value")
        if self.reference_type == ReferenceType.CATEGORICAL_THRESHOLDS and not self.categorical_thresholds:
            raise ValueError("reference_type CATEGORICAL_THRESHOLDS requires categorical_thresholds")
        return self


# --- CLASSIFICATION RULE ---

class ClassificationRule(BaseModel):
    """A clinical threshold/label set, kept separate from NormativeProfile's
    reference statistics. May carry its own source_id (a mean/SD and the
    clinical cutoff derived from it are not always the same evidence) and
    its own validation_status — a profile can be VALIDATED_FOR_PROFILE while
    its classification interpretation remains UNDER_REVIEW, or vice versa.
    """
    model_config = ConfigDict(extra="forbid")

    rule_id: str
    measurement_id: str
    measurement_definition_version: str
    profile_id: Optional[str] = None
    thresholds: List[float] = Field(min_length=1)
    labels: List[str] = Field(min_length=1)
    source_id: Optional[str] = None
    validation_status: ValidationStatus
    origin: CodeOrigin
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _labels_outnumber_thresholds_by_one(self) -> "ClassificationRule":
        if len(self.labels) != len(self.thresholds) + 1:
            raise ValueError(
                "labels must have exactly one more entry than thresholds "
                "(N thresholds partition the value line into N+1 labeled bands)"
            )
        return self


# --- NORMATIVE CONTEXT (Phase 3 service input — not persisted registry data) ---

class NormativeContext(BaseModel):
    """What the caller knows about the patient at evaluation time, passed in
    explicitly. The normative service never reads the patient database
    itself — no field here beyond what cephalo_normative_service.py's
    matching logic actually consumes (age, sex, population_id). Missing
    fields are `None`, never defaulted by this type or by the service.
    """
    model_config = ConfigDict(extra="forbid")

    age: Optional[float] = None
    sex: Optional[Sex] = None
    population_id: Optional[str] = None


# --- PLAUSIBILITY BOUNDS ---

class PlausibilityBounds(BaseModel):
    """Physiological safety bounds — deliberately separate from
    NormativeProfile. These apply unconditionally, even when no normative
    profile matches a patient's age/sex/population, because they represent
    "anatomically possible for any human", not a population norm.

    Keyed by bounds_id, not just measurement_id: the same measurement can
    have more than one bound origin (e.g. the validator's own bound and a
    frontend card's duplicated hard range each get their own row).
    """
    model_config = ConfigDict(extra="forbid")

    bounds_id: str
    measurement_id: str
    hard_min: float
    hard_max: float
    soft_min: float
    soft_max: float
    origin: CodeOrigin
    notes: Optional[str] = None

    @model_validator(mode="after")
    def _bounds_are_ordered(self) -> "PlausibilityBounds":
        if not (self.hard_min <= self.soft_min <= self.soft_max <= self.hard_max):
            raise ValueError(
                "bounds must satisfy hard_min <= soft_min <= soft_max <= hard_max"
            )
        return self
