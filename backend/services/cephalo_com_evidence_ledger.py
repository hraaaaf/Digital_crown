"""Fail-closed COM/CRANIOM historical evidence ledger.

Research/debt inventory only. It does not expose patient classification,
diagnosis, treatment indication, or normative runtime activation.

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
    SOURCE_LOCKED_MANUAL_CONSTRUCTION_AVAILABLE = (
        "SOURCE_LOCKED_MANUAL_CONSTRUCTION_AVAILABLE"
    )
    PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED = "PRIMARY_IDENTIFIED_NUMERIC_UNVERIFIED"
    PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING = (
        "PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING"
    )
    HISTORICAL_ATTRIBUTION_CONFLICT_PRIMARY_REVIEW_REQUIRED = (
        "HISTORICAL_ATTRIBUTION_CONFLICT_PRIMARY_REVIEW_REQUIRED"
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
        "STEINER_1953": MappingProxyType(
            {
                "citation": (
                    "Steiner CC. Cephalometrics for you and me. "
                    "Am J Orthod. 1953;39(10):729-755."
                ),
                "source_level": "PRIMARY_IDENTIFIED",
                "doi": "10.1016/0002-9416(53)90082-7",
            }
        ),
        "SANGALLI_2022_SYSTEMATIC_REVIEW": MappingProxyType(
            {
                "citation": (
                    "Sangalli L, et al. Proposed parameters of optimal central incisor "
                    "positioning in orthodontic treatment planning: A systematic "
                    "review. Korean J Orthod. 2022;52(1):53-65."
                ),
                "source_level": "SYSTEMATIC_REVIEW",
                "doi": "10.4041/kjod.2022.52.1.53",
                "evidence": (
                    "The review tabulates Steiner 1953 interincisal reference near "
                    "130 degrees and Downs historical data at 135.4 +/- 5.8 degrees, "
                    "which conflicts with later 131 +/- 3 attributions."
                ),
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
        "RICKETTS_1981_CLINICAL_CEPHALOMETRICS": MappingProxyType(
            {
                "citation": (
                    "Ricketts RM. Perspectives in the clinical application of "
                    "cephalometrics: the first fifty years. Angle Orthod. "
                    "1981;51(2):115-150."
                ),
                "source_level": "PRIMARY",
                "doi": "10.1043/0003-3219(1981)051<0115:PITCAO>2.0.CO;2",
                "evidence": (
                    "Ricketts' Summary Descriptive Analysis cue sheet gives the "
                    "mandibular plane as true Frankfort horizontal to Subgonion-Menton, "
                    "28 +/- 4 degrees at age 3, decreasing 1 degree each 3 years to "
                    "maturity; therefore age 9 is 26 +/- 4 degrees. True Frankfort is "
                    "source-specific and must not be silently replaced by generic "
                    "automatic Po-Or geometry."
                ),
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
        "COM_OVERJET_1P5_3_MM",
        "Surplomb",
        "1.5-3 mm",
        ComEvidenceState.POPULATION_REFERENCE_REQUIRED,
        (),
        "FH_PROJECTED_OVERJET_V1",
        "VERSIONED_POPULATION_REFERENCE_REQUIRED",
        "Historical interval is plausible but population-, age-, and protocol-dependent; no exact universal source is locked.",
        "Recover the historical source or register an explicitly versioned population reference without presenting it as universal.",
    ),
    ComEvidenceDebt(
        "COM_OVERBITE_1P5_3_MM",
        "Recouvrement",
        "1.5-3 mm",
        ComEvidenceState.POPULATION_REFERENCE_REQUIRED,
        (),
        "FH_PROJECTED_OVERBITE_V1",
        "VERSIONED_POPULATION_REFERENCE_REQUIRED",
        "Historical interval is plausible but population-, age-, and protocol-dependent; no exact universal source is locked.",
        "Recover the historical source or register an explicitly versioned population reference without presenting it as universal.",
    ),
    ComEvidenceDebt(
        "COM_IMPA_90_PM5",
        "IMPA",
        "90 +/- 5 deg",
        ComEvidenceState.SOURCE_LOCKED_CONSTRUCTION_BLOCKED,
        ("TWEED_1954_FMIA",),
        "TWEED_MANDIBULAR_PLANE_EXACT_REQUIRED",
        "TWEED_HISTORICAL_CONTEXT_ONLY",
        "Primary Tweed numeric evidence is locked, but the source-specific lower-border tangent and historical Frankfort construction are not represented; current Go-Me/Go-Gn and unproved generic Po-Or substitutions are forbidden.",
        "Version a clinician-audited source-specific Tweed tracing contract for the historical Frankfort reference and lower-border tangent before binding the 85-95 degree historical range.",
    ),
    ComEvidenceDebt(
        "COM_IMPA_DYNAMIC_COMPENSATION",
        "Compensation IMPA",
        "dynamic rule; historical shorthand 80-100 deg not accepted",
        ComEvidenceState.SOURCE_LOCKED_RULE_CONSTRUCTION_BLOCKED,
        ("TWEED_1954_FMIA",),
        "TWEED_FMA_AND_MANDIBULAR_PLANE_EXACT_REQUIRED",
        "TWEED_HISTORICAL_CONTEXT_ONLY",
        "Tweed directly describes a dynamic rule, not a universal fixed 80-100 degree interval; source-specific historical Frankfort and lower-border tangent geometry are still unbound.",
        "After the exact Tweed tracing contract is versioned, encode the source-specific rule: target IMPA decreases one degree for each degree FMA exceeds 25; include FMA 35 -> IMPA 80 golden.",
    ),
    ComEvidenceDebt(
        "COM_U1_FH_107_PM5",
        "U1-FH",
        "107 +/- 5 deg",
        ComEvidenceState.PEER_REVIEWED_CORROBORATED_PRIMARY_PENDING,
        ("BALLARD_EASTMAN_LINEAGE",),
        "FH_PO_OR_PLUS_U1_AXIS_EXACT_REQUIRED",
        "EASTMAN_BALLARD_CONTEXT_REQUIRED",
        "The value is clinically corroborated, but exact primary derivation and dispersion for U1-to-Frankfort remain open; Eastman UI/maxillary-plane values are not interchangeable.",
        "Recover the primary source explicitly defining Frankfort, U1 axis, 107 degrees, and dispersion.",
    ),
    ComEvidenceDebt(
        "COM_U1_FH_COMP_97_120",
        "Compensation U1-FH",
        "97-120 deg",
        ComEvidenceState.PRIMARY_SOURCE_NOT_FOUND,
        (),
        "FH_PO_OR_PLUS_U1_AXIS_EXACT_REQUIRED",
        None,
        "Targeted research did not recover a reliable exact source for 97-120 degrees.",
        "Search original COM-school archives; do not derive this interval arithmetically from 107 +/- 5 or CRANIOM extremes.",
    ),
    ComEvidenceDebt(
        "COM_INTERINCISAL_131_PM3",
        "Inter-incisif",
        "131 +/- 3 deg",
        ComEvidenceState.HISTORICAL_ATTRIBUTION_CONFLICT_PRIMARY_REVIEW_REQUIRED,
        ("DOWNS_1948", "STEINER_1953", "SANGALLI_2022_SYSTEMATIC_REVIEW"),
        "U1_AXIS_L1_AXIS_EXACT_REQUIRED",
        "SOURCE_SPECIFIC_HISTORICAL_CONTEXT_REQUIRED",
        "Available evidence conflicts: a 2022 systematic review reports Steiner near 130 degrees and Downs at 135.4 +/- 5.8 degrees, while later historical/teaching sources circulate 131 +/- 3 with inconsistent Downs/Steiner attribution. Direct primary tables have not yet source-locked 131 +/- 3.",
        "Inspect Downs 1948 and Steiner 1953/1959 primary tables/text directly, lock the exact construction and dispersion source-by-source, and never collapse conflicting conventions into one COM norm.",
    ),
    ComEvidenceDebt(
        "COM_INTERINCISAL_COMP_120_142",
        "Compensation inter-incisif",
        "120-142 deg",
        ComEvidenceState.PRIMARY_SOURCE_NOT_FOUND,
        (),
        "U1_AXIS_L1_AXIS_EXACT_REQUIRED",
        None,
        "No reliable exact primary or peer-reviewed source for 120-142 degrees was recovered.",
        "Search original COM-school archives; never reconstruct this range from 131 +/- 3, 131 +/- 5, 130 +/- 6, or another convention.",
    ),
    ComEvidenceDebt(
        "COM_FMA_26_PM4",
        "FMA",
        "26 +/- 4 deg at age 9",
        ComEvidenceState.SOURCE_LOCKED_MANUAL_CONSTRUCTION_AVAILABLE,
        ("RICKETTS_1981_CLINICAL_CEPHALOMETRICS", "RICKETTS_1960"),
        "RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V2",
        "RICKETTS_AGE_DEPENDENT_HISTORICAL_CONTEXT",
        "Primary Ricketts 1981 evidence source-locks the numeric/age rule and true Frankfort to Subgonion-Menton construction. Digital Crown exposes a fail-closed raw-measurement path only when RickettsTruePo, RickettsTrueOr, RickettsSubGo, and RickettsMe are explicit clinician-validated MANUAL landmarks from one image; generic SRPose38 Po/Or/Go/Me, Go-Me and Go-Gn remain forbidden substitutions.",
        "Keep patient classification inactive; use only RICKETTS_1981_FMA_TRUE_FH_SUBGO_ME_V2 for raw FMA, and certify any future automatic source-specific landmark mapping separately before norm activation.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_ABP_9Y",
        "A'B' 9 ans",
        "+4.2 +/- 3.2 mm",
        ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_AB_PRIME_V1",
        "CRANIOM_AGE_9_CONTEXT_REQUIRED",
        "Numeric value is reproduced technically but not yet read directly from the primary table.",
        "Recover the primary CRANIOM table row for A'B' at age 9.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_ABP_ADULT",
        "A'B' adulte",
        "+2.3 +/- 3.1 mm",
        ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_AB_PRIME_V1",
        "CRANIOM_ADULT_CONTEXT_REQUIRED",
        "Numeric value is reproduced technically but not yet read directly from the primary table.",
        "Recover the primary CRANIOM table row for adult A'B'.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_A_NVERT_9Y",
        "A / verticale N 9 ans",
        "+2.8 +/- 3.3 mm",
        ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_N_VERTICAL_OFFSET_V1",
        "CRANIOM_AGE_9_CONTEXT_REQUIRED",
        "Numeric value is reproduced technically but not yet read directly from the primary table.",
        "Recover the primary CRANIOM table row for A/N vertical at age 9.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_A_NVERT_ADULT",
        "A / verticale N adulte",
        "+2.3 +/- 3.0 mm; secondary divergence +/- 3.3",
        ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_N_VERTICAL_OFFSET_V1",
        "CRANIOM_ADULT_CONTEXT_REQUIRED",
        "Secondary reproductions diverge on SD (3.0 vs 3.3 mm).",
        "Resolve the 3.0/3.3 mm SD directly against the original primary table.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_B_NVERT_9Y",
        "B / verticale N 9 ans",
        "-1.5 +/- 4.5 mm",
        ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_N_VERTICAL_OFFSET_V1",
        "CRANIOM_AGE_9_CONTEXT_REQUIRED",
        "Numeric value is reproduced technically but not yet read directly from the primary table.",
        "Recover the primary CRANIOM table row for B/N vertical at age 9.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_B_NVERT_ADULT",
        "B / verticale N adulte",
        "0.0 +/- 4.9 mm",
        ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_N_VERTICAL_OFFSET_V1",
        "CRANIOM_ADULT_CONTEXT_REQUIRED",
        "Numeric value is reproduced technically but not yet read directly from the primary table.",
        "Recover the primary CRANIOM table row for adult B/N vertical.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_S_NVERT_DEPTH_9Y",
        "S / verticale N profondeur 9 ans",
        "61.3 +/- 5 mm; text rounding 62 +/- 5",
        ComEvidenceState.SECONDARY_NUMERIC_DIVERGENCE_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_FACIAL_DEPTH_MM_V1",
        "CRANIOM_AGE_9_CONTEXT_REQUIRED",
        "Secondary material diverges between tabular 61.3 and rounded textual 62 mm.",
        "Resolve the table value and construction semantics directly in the primary source.",
    ),
    ComEvidenceDebt(
        "COM_CRANIOM_S_NVERT_DEPTH_ADULT",
        "S / verticale N profondeur adulte",
        "70.3 +/- 5 mm",
        ComEvidenceState.SECONDARY_NUMERIC_PRIMARY_PENDING,
        ("CRANIOM_PART2_2011", "CRANIOM_TECHNICAL_REPRODUCTION"),
        "CRANIOM_FACIAL_DEPTH_MM_V1",
        "CRANIOM_ADULT_CONTEXT_REQUIRED",
        "Numeric value is reproduced technically but not yet read directly from the primary table.",
        "Recover the adult facial-depth row directly from the primary table and certify geometry.",
    ),
)


COM_EVIDENCE_DEBT_BY_ID: Mapping[str, ComEvidenceDebt] = MappingProxyType(
    {item.debt_id: item for item in COM_EVIDENCE_DEBTS}
)


def patient_classification_references() -> Tuple[ComEvidenceDebt, ...]:
    """Return active COM debt rows; intentionally empty until reviewed activation."""

    return tuple(
        item for item in COM_EVIDENCE_DEBTS if item.active_for_patient_classification
    )
