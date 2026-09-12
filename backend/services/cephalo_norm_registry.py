"""Versioned cephalometric normative-reference registry.

This module stores scientific reference metadata. It deliberately does NOT
classify patients, diagnose malocclusion, infer treatment, or promote a
published sample into a universal norm.

Numerical references are inert by default. Activation for patient-specific
interpretation is a separate, clinician-reviewed gate.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple


class SourceTier(str, Enum):
    PRIMARY_ARTICLE = "PRIMARY_ARTICLE"
    PEER_REVIEWED_POPULATION_STUDY = "PEER_REVIEWED_POPULATION_STUDY"
    PEER_REVIEWED_REVIEW = "PEER_REVIEWED_REVIEW"
    SECONDARY_TECHNICAL = "SECONDARY_TECHNICAL"


class ReferenceKind(str, Enum):
    EXTREME_RANGE = "EXTREME_RANGE"
    MEAN_SD = "MEAN_SD"
    PERCENTILE = "PERCENTILE"


PRIMARY_NUMERIC_TIERS = frozenset(
    {
        SourceTier.PRIMARY_ARTICLE,
        SourceTier.PEER_REVIEWED_POPULATION_STUDY,
    }
)
SUPPORTED_REFERENCE_KINDS = frozenset(
    {ReferenceKind.EXTREME_RANGE, ReferenceKind.MEAN_SD}
)


@dataclass(frozen=True)
class NormSource:
    source_id: str
    tier: SourceTier
    citation: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None
    sample_description: Optional[str] = None
    applicability_note: Optional[str] = None


@dataclass(frozen=True)
class NormReference:
    reference_id: str
    method_id: str
    method_version: str
    measurement_id: str
    kind: ReferenceKind
    unit: str
    lower: Optional[float]
    upper: Optional[float]
    source_ids: Tuple[str, ...]
    population_context: Mapping[str, str]
    mean: Optional[float] = None
    sd: Optional[float] = None
    construction_gate: Optional[str] = None
    active_for_patient_classification: bool = False
    note: Optional[str] = None


class NormRegistry:
    """Small immutable-by-copy registry with fail-closed registration gates."""

    def __init__(self) -> None:
        self._sources: Dict[str, NormSource] = {}
        self._references: Dict[str, NormReference] = {}

    @staticmethod
    def _nonempty(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be non-empty")

    @staticmethod
    def _validate_numeric_shape(reference: NormReference) -> None:
        if reference.kind == ReferenceKind.EXTREME_RANGE:
            if reference.lower is None or reference.upper is None:
                raise ValueError("EXTREME_RANGE requires lower and upper limits")
            if reference.mean is not None or reference.sd is not None:
                raise ValueError("EXTREME_RANGE cannot define mean or sd")
            if not math.isfinite(reference.lower) or not math.isfinite(reference.upper):
                raise ValueError("Normative range limits must be finite")
            if reference.lower > reference.upper:
                raise ValueError("Normative range lower limit cannot exceed upper limit")
            return

        if reference.kind == ReferenceKind.MEAN_SD:
            if reference.mean is None or reference.sd is None:
                raise ValueError("MEAN_SD requires mean and sd")
            if reference.lower is not None or reference.upper is not None:
                raise ValueError("MEAN_SD cannot define lower or upper limits")
            if not math.isfinite(reference.mean) or not math.isfinite(reference.sd):
                raise ValueError("MEAN_SD values must be finite")
            if reference.sd <= 0:
                raise ValueError("MEAN_SD sd must be strictly positive")
            return

        raise ValueError(f"Unsupported normative reference kind: {reference.kind.value}")

    def register_source(self, source: NormSource) -> None:
        self._nonempty(source.source_id, "source_id")
        self._nonempty(source.citation, "citation")
        if source.source_id in self._sources:
            raise ValueError(f"Duplicate normative source: {source.source_id}")
        self._sources[source.source_id] = source

    def register_reference(self, reference: NormReference) -> None:
        self._nonempty(reference.reference_id, "reference_id")
        self._nonempty(reference.method_id, "method_id")
        self._nonempty(reference.method_version, "method_version")
        self._nonempty(reference.measurement_id, "measurement_id")
        self._nonempty(reference.unit, "unit")
        if reference.reference_id in self._references:
            raise ValueError(f"Duplicate normative reference: {reference.reference_id}")
        if reference.kind not in SUPPORTED_REFERENCE_KINDS:
            raise ValueError(
                "Registry currently supports only EXTREME_RANGE and MEAN_SD references"
            )
        if not reference.source_ids:
            raise ValueError("Normative reference requires at least one source")
        missing_sources = [sid for sid in reference.source_ids if sid not in self._sources]
        if missing_sources:
            raise ValueError(f"Unknown normative source(s): {', '.join(missing_sources)}")

        resolved_sources = [self._sources[sid] for sid in reference.source_ids]
        if not any(source.tier in PRIMARY_NUMERIC_TIERS for source in resolved_sources):
            raise ValueError(
                "Numeric normative reference requires at least one primary research source"
            )
        self._validate_numeric_shape(reference)
        if not reference.population_context:
            raise ValueError("Normative reference requires explicit population context")
        if reference.active_for_patient_classification:
            raise ValueError(
                "Registry foundation does not permit direct activation for patient classification"
            )

        frozen_context = MappingProxyType(dict(reference.population_context))
        self._references[reference.reference_id] = NormReference(
            reference_id=reference.reference_id,
            method_id=reference.method_id,
            method_version=reference.method_version,
            measurement_id=reference.measurement_id,
            kind=reference.kind,
            unit=reference.unit,
            lower=reference.lower,
            upper=reference.upper,
            source_ids=tuple(reference.source_ids),
            population_context=frozen_context,
            mean=reference.mean,
            sd=reference.sd,
            construction_gate=reference.construction_gate,
            active_for_patient_classification=False,
            note=reference.note,
        )

    @property
    def sources(self) -> Mapping[str, NormSource]:
        return MappingProxyType(dict(self._sources))

    @property
    def references(self) -> Mapping[str, NormReference]:
        return MappingProxyType(dict(self._references))

    def get_source(self, source_id: str) -> Optional[NormSource]:
        return self._sources.get(source_id)

    def get_reference(self, reference_id: str) -> Optional[NormReference]:
        return self._references.get(reference_id)


registry = NormRegistry()

registry.register_source(
    NormSource(
        source_id="CRANIOM_PART1_2010",
        tier=SourceTier.PRIMARY_ARTICLE,
        citation=(
            "Bonnefont R, Casteigt J, Ernoult J-F, Sorel O. A new method for the "
            "utilization of cephalometric measurements in orthodontics or how "
            "standard deviations can sometimes be the practitioner's false friends "
            "(Part 1). J Dentofacial Anom Orthod. 2010;13(4):385-400."
        ),
        doi="10.1051/odfen/2010406",
        sample_description="83 untreated young adults with Class I occlusion",
        applicability_note=(
            "CRANIOM method-specific reference sample; not a universal population norm."
        ),
    )
)
registry.register_source(
    NormSource(
        source_id="CRANIOM_PART2_2011",
        tier=SourceTier.PRIMARY_ARTICLE,
        citation=(
            "Bonnefont R, Ernoult J-F, Sorel O. A new method of using cephalometric "
            "measurements in orthodontics (part 2) or how standard deviations can "
            "be the practitioner's false friends. J Dentofacial Anom Orthod. "
            "2011;14:105."
        ),
        doi="10.1051/odfen/2011104",
        sample_description="83 untreated young adults with Class I occlusion",
        applicability_note=(
            "Primary source explicitly uses broad observed extremes and places "
            "cephalometrics after esthetic, periodontal and muscular assessment."
        ),
    )
)
registry.register_source(
    NormSource(
        source_id="CRANIOM_TECHNICAL_REPRODUCTION",
        tier=SourceTier.SECONDARY_TECHNICAL,
        citation="Technical CRANIOM/ODRADE cephalometry teaching document.",
        url="https://www.slot-concept.com/bases/slot_communication_pdf/7/fichier.pdf",
        applicability_note=(
            "Secondary source. Values not present in an accessible primary source "
            "must remain inactive pending primary-source verification."
        ),
    )
)
registry.register_source(
    NormSource(
        source_id="MOROCCO_STEINER_OUSEHAL_2012",
        tier=SourceTier.PEER_REVIEWED_POPULATION_STUDY,
        citation=(
            "Ousehal L, Lazrak L, Chafii A. Cephalometric norms for a Moroccan "
            "population. Int Orthod. 2012;10(1):122-134."
        ),
        doi="10.1016/j.ortho.2011.12.001",
        pmid="22236522",
        sample_description=(
            "71 young adults aged 19-27 from the CCTD Casablanca patient population; "
            "47 women, 24 men; facial harmony, acceptable profile, Class I, untreated"
        ),
        applicability_note=(
            "Authors caution that the sample should not be generalized to Casablanca "
            "or Morocco as a whole without more exhaustive studies."
        ),
    )
)
registry.register_source(
    NormSource(
        source_id="MCNAMARA_1984",
        tier=SourceTier.PRIMARY_ARTICLE,
        citation=(
            "McNamara JA Jr. A method of cephalometric evaluation. "
            "Am J Orthod. 1984;86(6):449-469."
        ),
        doi="10.1016/S0002-9416(84)90352-X",
        pmid="6594933",
        url=(
            "https://media.dent.umich.edu/labs/mcnamara/files/"
            "A%20method%20of%20cephalometric%20evaluation.pdf"
        ),
        sample_description=(
            "Ann Arbor Table I: 111 untreated adults with well-balanced faces and "
            "good occlusions; 73 women and 38 men; Class I, good skeletal balance, "
            "orthognathic facial profile"
        ),
        applicability_note=(
            "The article states that, whenever possible, measures from its reference "
            "samples include an 8% enlargement factor. Linear Table I values must not "
            "be compared with calibrated physical millimetres until scale compatibility "
            "is explicitly established."
        ),
    )
)
registry.register_source(
    NormSource(
        source_id="PEDIATRIC_NORMS_REVIEW_NGUYEN_2024",
        tier=SourceTier.PEER_REVIEWED_REVIEW,
        citation=(
            "Nguyen TK, Cambala A, Hrit M, Zimmermann EA. A scoping review of "
            "cephalometric normative data in children. Korean J Orthod. 2024;54(4):210-228."
        ),
        pmid="38898629",
        applicability_note=(
            "Supports age/development-aware handling of pediatric reference data; "
            "does not justify one universal child norm."
        ),
    )
)

registry.register_reference(
    NormReference(
        reference_id="CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1",
        method_id="CRANIOM",
        method_version="2010-2011",
        measurement_id="L1_TO_DOWNS_MP_ANGLE",
        kind=ReferenceKind.EXTREME_RANGE,
        unit="deg",
        lower=78.0,
        upper=114.0,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        population_context=MappingProxyType(
            {
                "age_group": "young_adult",
                "occlusion": "Class I",
                "orthodontic_treatment_history": "none",
                "sample_size": "83",
            }
        ),
        construction_gate="DOWNS_MP_TANGENT",
        active_for_patient_classification=False,
        note=(
            "Reference interval described by CRANIOM observed extremes; exact Downs "
            "mandibular-plane construction must be available before computation."
        ),
    )
)
registry.register_reference(
    NormReference(
        reference_id="CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1",
        method_id="CRANIOM",
        method_version="2010-2011",
        measurement_id="U1_TO_FRANKFORT_ANGLE",
        kind=ReferenceKind.EXTREME_RANGE,
        unit="deg",
        lower=97.5,
        upper=130.1,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        population_context=MappingProxyType(
            {
                "age_group": "young_adult",
                "occlusion": "Class I",
                "orthodontic_treatment_history": "none",
                "sample_size": "83",
            }
        ),
        construction_gate="FH_PO_OR_V1",
        active_for_patient_classification=False,
        note="Method-specific CRANIOM observed-extremes interval; descriptive only.",
    )
)

_MCNAMARA_COMMON_CONTEXT = {
    "site": "Ann Arbor, Michigan",
    "treatment_status": "untreated",
    "occlusion": "Class I",
    "skeletal_balance": "good",
    "facial_profile": "orthognathic; good to excellent facial configuration",
    "radiographic_scale": "8% enlargement factor included whenever possible",
    "scale_compatibility": "BLOCKED_UNTIL_8_PERCENT_ENLARGEMENT_MATCHED",
}


def _mcnamara_context(*, sex: str, sample_size: str, mean_age: str) -> Mapping[str, str]:
    return MappingProxyType(
        {
            **_MCNAMARA_COMMON_CONTEXT,
            "sex": sex,
            "sample_size": sample_size,
            "mean_age": mean_age,
        }
    )


# Table I values are directly sourced from McNamara 1984. Registry binding
# follows the evidence-graph contract: method_id targets MeasurementEvidence.analysis_id
# and measurement_id targets MeasurementEvidence.method_id. The references remain
# descriptive because the source carries an 8% enlargement convention while the
# runtime measurements are calibrated physical millimetres.
_MCNAMARA_TABLE_I_REFERENCES = (
    (
        "MCNAMARA_CO_GN_ANN_ARBOR_FEMALE_MEAN_SD_V1",
        "MCNAMARA_CO_GN_MM_V1",
        "MCNAMARA_CO_GN_V1",
        "female",
        "73",
        "26 years 8 months",
        120.2,
        5.3,
    ),
    (
        "MCNAMARA_CO_GN_ANN_ARBOR_MALE_MEAN_SD_V1",
        "MCNAMARA_CO_GN_MM_V1",
        "MCNAMARA_CO_GN_V1",
        "male",
        "38",
        "30 years 9 months",
        134.3,
        6.8,
    ),
    (
        "MCNAMARA_CO_A_ANN_ARBOR_FEMALE_MEAN_SD_V1",
        "MCNAMARA_CO_A_MM_V1",
        "MCNAMARA_CO_A_V1",
        "female",
        "73",
        "26 years 8 months",
        91.0,
        4.3,
    ),
    (
        "MCNAMARA_CO_A_ANN_ARBOR_MALE_MEAN_SD_V1",
        "MCNAMARA_CO_A_MM_V1",
        "MCNAMARA_CO_A_V1",
        "male",
        "38",
        "30 years 9 months",
        99.8,
        6.0,
    ),
    (
        "MCNAMARA_ANS_ME_ANN_ARBOR_FEMALE_MEAN_SD_V1",
        "MCNAMARA_ANS_ME_MM_V1",
        "MCNAMARA_ANS_ME_V1",
        "female",
        "73",
        "26 years 8 months",
        66.7,
        4.1,
    ),
    (
        "MCNAMARA_ANS_ME_ANN_ARBOR_MALE_MEAN_SD_V1",
        "MCNAMARA_ANS_ME_MM_V1",
        "MCNAMARA_ANS_ME_V1",
        "male",
        "38",
        "30 years 9 months",
        74.6,
        5.0,
    ),
)

for (
    reference_id,
    measurement_method_id,
    construction_gate,
    sex,
    sample_size,
    mean_age,
    mean,
    sd,
) in _MCNAMARA_TABLE_I_REFERENCES:
    registry.register_reference(
        NormReference(
            reference_id=reference_id,
            method_id="MCNAMARA",
            method_version="1",
            measurement_id=measurement_method_id,
            kind=ReferenceKind.MEAN_SD,
            unit="mm",
            lower=None,
            upper=None,
            source_ids=("MCNAMARA_1984",),
            population_context=_mcnamara_context(
                sex=sex,
                sample_size=sample_size,
                mean_age=mean_age,
            ),
            mean=mean,
            sd=sd,
            construction_gate=construction_gate,
            active_for_patient_classification=False,
            note=(
                "Primary Table I Ann Arbor reference; descriptive only. Do not compare "
                "with Digital Crown calibrated physical millimetres until the source's "
                "8% enlargement convention is explicitly matched."
            ),
        )
    )
