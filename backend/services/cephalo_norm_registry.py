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
    lower: float
    upper: float
    source_ids: Tuple[str, ...]
    population_context: Mapping[str, str]
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
        if not math.isfinite(reference.lower) or not math.isfinite(reference.upper):
            raise ValueError("Normative range limits must be finite")
        if reference.lower > reference.upper:
            raise ValueError("Normative range lower limit cannot exceed upper limit")
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

# Primary CRANIOM publications.
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

# Secondary technical reproduction: useful for provenance/cross-checking only.
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

# Population context relevant to the Moroccan deployment, registered without
# copying unverified table values into the runtime registry.
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

# Exact ranges below are present in the accessible primary abstract of CRANIOM
# Part 2 and cross-checked against the technical reproduction. They remain inert.
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
