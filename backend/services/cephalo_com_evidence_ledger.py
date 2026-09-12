"""Fail-closed COM/CRANIOM historical evidence ledger.

This module is a research/debt inventory only. It deliberately does not expose
patient classification, diagnosis, treatment indication, or normative runtime
activation. A row may become source-locked while remaining blocked on geometry,
population applicability, or direct primary numeric verification.

Scientific invariant:
    measurement != reference != finding != diagnosis != indication != treatment

No-drop invariant:
    BLOCKED != DROPPED
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping, Optional, Tuple


class ComEvidenceState(str, Enum):
    SOURCE_LOCKED_CONSTRUCTION_BLOCKED = "SOURCE_LOCKED_CONSTRUCTION_BLOCKED"
    SOURCE_LOCKED_RULE_CONSTRUCTION_BLOCKED = "SOURCE_LOCKED_RULE_CONSTRUCTION_BLOCKED"
    PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED = "PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED"
    PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING = (
        "PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING"
    )
    POPULATION_REFERENCE_REQUIRED = "POPULATION_REFERENCE_REQUIRED"
    PRIMARY_SOURCE_NOT_FOUND = "PRIMARY_SOURCE_NOT_FOUND"
    SECONDARY_NUMERIC_PRIMARY_PENDING = "SECONDARY_NUMERIC_PRIMARY_PENDING"
    SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING = (
        "SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING"
    )


@dataclass(frozen=True)
class ComEvidenceDebt:
    debt_id: str
    label: str
    historical_value: str
    state: ComEvidenceState
    source_ids: Tuple[str, ...]
    construction_gate: Optional[str]
    population_gate: Optional[str]
    blocker: str
    next_exact: str
    active_for_patient_classification: bool = False


# Primary/strong sources already present elsewhere in the scientific corpus.
# IDs here are traceability handles, not runtime activation handles.
COM_SOURCE_INDEX: Mapping[str, Mapping[str, str]] = MappingProxyType(
    {
        "TWEED_1954_FMIA": MappingProxyType(
            {
                "citation": (
                    "Tweed CH. The Frankfort-mandibular incisor angle (FMIA) in "
                    "orthodontic diagnosis, treatment planning and prognosis. "
                    "Angle Orthod. 1954;24(3):121-169."
                ),
                "source_level": "PRIMARY",
                "evidence": (
                    "Primary text states FMA normal variation 20-30 degrees with "
                    "25-degree historical norm, mandibular-incisor inclination "
                    "85-95 degrees with 90-degree historical norm, and the dynamic "
                    "one-degree IMPA compensation for each degree FMA exceeds 25."
                ),
            }
        ),
        "DOWNS_1948": MappingProxyType(
            {
                "citation": (
                    "Downs WB. Variations in facial relationships; their significance "
                    "in treatment and prognosis. Am J Orthod. 1948;34(10):812-840."
                ),
                "source_level": "PRIMARY_IDENTIFIED",
                "doi": "10.1016/0002-9416(48)90015-3",
            }
        ),
        "RICKETTS_1960": MappingProxyType(
            {
                "citation": (
                    "Ricketts RM. A foundation for cephalometric communication. "
                    "Am J Orthod. 1960;46(5):330-357."
                ),
                "source_level": "PRIMARY_IDENTIFIED",
                "doi": "10.1016/0002-9416(60)90047-6",
            }
        ),
        "CRANIOM_PART2_2011": MappingProxyType(
            {
                "citation": (
                    "Bonnefont R, Ernoult J-F, Sorel O. A new method of using "
                    "cephalometric measurements in orthodontics (part 2). "
                    "J Dentofacial Anom Orthod. 2011;14:105."
                ),
                "source_level": "PRIMARY",
                "doi": "10.1051/odfen/2011104",
            }
        ),
        "CRANIOM_TECHNICAL_REPRODUCTION": MappingProxyType(
            {
                "citation": "Technical CRANIOM/ODRADE teaching reproduction.",
                "source_level": "SECONDARY_TECHNICAL",
            }
        ),
        "BALLARD_EASTMAN_LINEAGE": MappingProxyType(
            {
                "citation": (
                    "Ballard/Eastman historical lineage; exact U1-FH 107 +/- 5 "
                    "primary derivation not yet directly verified."
                ),
                "source_level": "HISTORICAL_LINEAGE",
            }
        ),
    }
)


COM_EVIDENCE_DEBTS: Tuple[ComEvidenceDebt, ...] = (
    ComEvidenceDebt(
        debt_id="COM_OVERJET_1P5_3_MM",
        label="Surplomb",
        historical_value="1.5-3 mm",
        state=ComEvidenceState.POPULATION_REFERENCE_REQUIRED,
        source_ids=(),
        construction_gate="FH_PROJECTED_OVERJET_V1",
        population_gate="VERSIONED_POPULATION_REFERENCE_REQUIRED",
        blocker=(
            "The historical interval is plausible but population-, age-, and protocol-"
            "dependent; no exact source for this universal interval is locked."
        ),
        next_exact=(
            "Recover the historical source or register an explicitly versioned "
            "population reference without presenting it as universal."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_OVERBITE_1P5_3_MM",
        label="Recouvrement",
        historical_value="1.5-3 mm",
        state=ComEvidenceState.POPULATION_REFERENCE_REQUIRED,
        source_ids=(),
        construction_gate="FH_PROJECTED_OVERBITE_V1",
        population_gate="VERSIONED_POPULATION_REFERENCE_REQUIRED",
        blocker=(
            "The historical interval is plausible but population-, age-, and protocol-"
            "dependent; no exact source for this universal interval is locked."
        ),
        next_exact=(
            "Recover the historical source or register an explicitly versioned "
            "population reference without presenting it as universal."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_IMPA_90_PM5",
        label="IMPA",
        historical_value="90 +/- 5 deg",
        state=ComEvidenceState.SOURCE_LOCKED_CONSTRUCTION_BLOCKED,
        source_ids=("TWEED_1954_FMIA",),
        construction_gate="TWEED_MANDIBULAR_PLANE_EXACT_REQUIRED",
        population_gate="TWEED_HISTORICAL_CONTEXT_ONLY",
        blocker=(
            "Primary Tweed numeric evidence is locked, but equivalence between the "
            "Tweed lower-border mandibular plane and the current runtime Go-Me line "
            "has not been proven."
        ),
        next_exact=(
            "Lock the exact Tweed mandibular-plane construction; only then bind the "
            "85-95 degree historical range to a versioned measurement method."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_IMPA_DYNAMIC_COMPENSATION",
        label="Compensation IMPA",
        historical_value="dynamic rule; historical shorthand 80-100 deg not accepted",
        state=ComEvidenceState.SOURCE_LOCKED_RULE_CONSTRUCTION_BLOCKED,
        source_ids=("TWEED_1954_FMIA",),
        construction_gate="TWEED_FMA_AND_MANDIBULAR_PLANE_EXACT_REQUIRED",
        population_gate="TWEED_HISTORICAL_CONTEXT_ONLY",
        blocker=(
            "Tweed directly describes a dynamic rule, not a universal fixed 80-100 "
            "degree normative interval; exact Tweed geometry is still unbound."
        ),
        next_exact=(
            "After construction lock, encode the source-specific rule: target IMPA "
            "decreases one degree for each degree FMA exceeds 25; test goldens such "
            "as FMA 35 -> IMPA 80."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_U1_FH_107_PM5",
        label="U1-FH",
        historical_value="107 +/- 5 deg",
        state=ComEvidenceState.PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING,
        source_ids=("BALLARD_EASTMAN_LINEAGE",),
        construction_gate="FH_PO_OR_PLUS_U1_AXIS_EXACT_REQUIRED",
        population_gate="EASTMAN_BALLARD_CONTEXT_REQUIRED",
        blocker=(
            "The value is corroborated in peer-reviewed clinical literature, but the "
            "exact primary derivation and dispersion for U1-to-Frankfort remain open; "
            "Eastman UI/maxillary-plane values are not interchangeable."
        ),
        next_exact=(
            "Recover the primary Ballard/Eastman source explicitly defining Frankfort, "
            "U1 axis, 107 degrees, and the reported dispersion."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_U1_FH_COMP_97_120",
        label="Compensation U1-FH",
        historical_value="97-120 deg",
        state=ComEvidenceState.PRIMARY_SOURCE_NOT_FOUND,
        source_ids=(),
        construction_gate="FH_PO_OR_PLUS_U1_AXIS_EXACT_REQUIRED",
        population_gate=None,
        blocker="Targeted research did not recover a reliable exact source for 97-120 degrees.",
        next_exact=(
            "Search original COM-school archives; do not derive this interval "
            "arithmetically from 107 +/- 5 or from CRANIOM extremes."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_INTERINCISAL_131_PM3",
        label="Inter-incisif",
        historical_value="131 +/- 3 deg",
        state=ComEvidenceState.PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED,
        source_ids=("DOWNS_1948",),
        construction_gate="U1_AXIS_L1_AXIS_EXACT_REQUIRED",
        population_gate="DOWNS_EXCELLENT_OCCLUSION_SAMPLE_CONTEXT",
        blocker=(
            "Downs 1948 is the primary article, and secondary historical attribution "
            "supports 131 +/- 3, but the exact number has not been reread directly in "
            "the primary table/text."
        ),
        next_exact="Verify the exact 131 +/- 3 value directly in the Downs 1948 primary text/table.",
    ),
    ComEvidenceDebt(
        debt_id="COM_INTERINCISAL_COMP_120_142",
        label="Compensation inter-incisif",
        historical_value="120-142 deg",
        state=ComEvidenceState.PRIMARY_SOURCE_NOT_FOUND,
        source_ids=(),
        construction_gate="U1_AXIS_L1_AXIS_EXACT_REQUIRED",
        population_gate=None,
        blocker="No reliable exact primary or peer-reviewed source for 120-142 degrees was recovered.",
        next_exact=(
            "Search original COM-school archives; never reconstruct this range from "
            "131 +/- 3, 131 +/- 5, 130 +/- 6, or another convention."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_FMA_26_PM4",
        label="FMA",
        historical_value="26 +/- 4 deg",
        state=ComEvidenceState.PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING,
        source_ids=("RICKETTS_1960",),
        construction_gate="RICKETTS_FH_GO_GN_EXACT_REQUIRED",
        population_gate="RICKETTS_AGE_CONTEXT_REQUIRED",
        blocker=(
            "26 +/- 4 is strongly attributed to Ricketts in peer-reviewed literature, "
            "but the numeric value/age correction has not been directly extracted "
            "from an accessible primary Ricketts table."
        ),
        next_exact=(
            "Lock the numeric reference and age contract directly from a primary "
            "Ricketts source, then certify the exact FH/mandibular-plane construction."
        ),
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_ABP_9Y",
        label="A'B' 9 ans",
        historical_value="+4.2 +/- 3.2 mm",
        state=ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_AB_PRIME_V1",
        population_gate="CRANIOM_AGE_9_CONTEXT_REQUIRED",
        blocker="Numeric value is reproduced technically but not yet read directly from the primary table.",
        next_exact="Recover the primary CRANIOM table row for A'B' at age 9.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_ABP_ADULT",
        label="A'B' adulte",
        historical_value="+2.3 +/- 3.1 mm",
        state=ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_AB_PRIME_V1",
        population_gate="CRANIOM_ADULT_CONTEXT_REQUIRED",
        blocker="Numeric value is reproduced technically but not yet read directly from the primary table.",
        next_exact="Recover the primary CRANIOM table row for adult A'B'.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_A_NVERT_9Y",
        label="A / verticale N 9 ans",
        historical_value="+2.8 +/- 3.3 mm",
        state=ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_N_VERTICAL_OFFSET_V1",
        population_gate="CRANIOM_AGE_9_CONTEXT_REQUIRED",
        blocker="Numeric value is reproduced technically but not yet read directly from the primary table.",
        next_exact="Recover the primary CRANIOM table row for A/N vertical at age 9.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_A_NVERT_ADULT",
        label="A / verticale N adulte",
        historical_value="+2.3 +/- 3.0 mm; secondary divergence +/- 3.3",
        state=ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_N_VERTICAL_OFFSET_V1",
        population_gate="CRANIOM_ADULT_CONTEXT_REQUIRED",
        blocker="Secondary reproductions diverge on SD (3.0 vs 3.3 mm).",
        next_exact="Resolve the 3.0/3.3 mm SD directly against the original primary table.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_B_NVERT_9Y",
        label="B / verticale N 9 ans",
        historical_value="-1.5 +/- 4.5 mm",
        state=ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_N_VERTICAL_OFFSET_V1",
        population_gate="CRANIOM_AGE_9_CONTEXT_REQUIRED",
        blocker="Numeric value is reproduced technically but not yet read directly from the primary table.",
        next_exact="Recover the primary CRANIOM table row for B/N vertical at age 9.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_B_NVERT_ADULT",
        label="B / verticale N adulte",
        historical_value="0.0 +/- 4.9 mm",
        state=ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_N_VERTICAL_OFFSET_V1",
        population_gate="CRANIOM_ADULT_CONTEXT_REQUIRED",
        blocker="Numeric value is reproduced technically but not yet read directly from the primary table.",
        next_exact="Recover the primary CRANIOM table row for adult B/N vertical.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_S_NVERT_DEPTH_9Y",
        label="S / verticale N profondeur 9 ans",
        historical_value="61.3 +/- 5 mm; text rounding 62 +/- 5",
        state=ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_FACIAL_DEPTH_MM_V1",
        population_gate="CRANIOM_AGE_9_CONTEXT_REQUIRED",
        blocker="Secondary material diverges between tabular 61.3 and rounded textual 62 mm.",
        next_exact="Resolve the table value and construction semantics directly in the primary source.",
    ),
    ComEvidenceDebt(
        debt_id="COM_CRANIOM_S_NVERT_DEPTH_ADULT",
        label="S / verticale N profondeur adulte",
        historical_value="70.3 +/- 5 mm",
        state=ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        source_ids=("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        construction_gate="CRANIOM_FACIAL_DEPTH_MM_V1",
        population_gate="CRANIOM_ADULT_CONTEXT_REQUIRED",
        blocker="Numeric value is reproduced technically but not yet read directly from the primary table.",
        next_exact="Recover the adult facial-depth row directly from the primary table and certify geometry.",
    ),
)


COM_EVIDENCE_DEBT_BY_ID: Mapping[str, ComEvidenceDebt] = MappingProxyType(
    {item.debt_id: item for item in COM_EVIDENCE_DEBTS}
)


def patient_classification_references() -> Tuple[ComEvidenceDebt, ...]:
    """Return active COM debt rows.

    Research debt must never silently become a clinical classifier. The function
    intentionally returns an empty tuple until a separate reviewed activation
    contract exists.
    """

    return tuple(
        item for item in COM_EVIDENCE_DEBTS if item.active_for_patient_classification
    )
