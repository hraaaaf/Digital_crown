"""Neo-Ordonnance N4.1 bounded medication evidence.

Evidence is fail-closed: bounded findings may be emitted, but this layer never
claims exhaustive interaction or contraindication coverage.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

EVIDENCE_VERSION = "2026-09-30.n4.1-v1"
SRC_AMOX_SANDOZ = "BDM_ANSM_RCP_67410088_7"
SRC_AMOX_TEVA = "BDM_ANSM_RCP_66748343_1"
SRC_IBU_BIOGARAN = "BDM_ANSM_RCP_68337369_4"
SRC_IBU_CRISTERS = "BDM_ANSM_RCP_65780135_5"
SOURCE_URLS = {
    SRC_AMOX_SANDOZ: "https://m.base-donnees-publique.medicaments.gouv.fr/rcp-67410088-7",
    SRC_AMOX_TEVA: "https://m.base-donnees-publique.medicaments.gouv.fr/rcp-66748343-1",
    SRC_IBU_BIOGARAN: "https://m.base-donnees-publique.medicaments.gouv.fr/rcp-68337369-4",
    SRC_IBU_CRISTERS: "https://m.base-donnees-publique.medicaments.gouv.fr/rcp-65780135-5",
}


@dataclass(frozen=True)
class EvidenceFinding:
    code: str
    severity: str
    source_ids: Tuple[str, ...]


@dataclass(frozen=True)
class EvidenceEvaluation:
    active_ingredient: str
    covered: bool
    # True means the domain was exhaustively evaluated for the supplied inputs.
    # N4.1 is deliberately bounded, so both completeness flags stay False.
    interaction_complete_for_inputs: bool
    contraindication_complete_for_inputs: bool
    findings: Tuple[EvidenceFinding, ...]
    source_ids: Tuple[str, ...]
    evidence_version: str = EVIDENCE_VERSION


def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).upper()
    return " ".join(re.findall(r"[A-Z0-9]+", text))


def canonical_active_ingredient(dci: str) -> str:
    value = _norm(dci)
    if value in {"AMOXICILLINE", "AMOXICILLIN"}:
        return "AMOXICILLIN"
    if value in {"IBUPROFENE", "IBUPROFEN"}:
        return "IBUPROFEN"
    return value


_MEDICATION_ALIASES = {
    "METHOTREXATE": ("METHOTREXATE",),
    "WARFARIN": ("WARFARIN", "WARFARINE"),
    "ACENOCOUMAROL": ("ACENOCOUMAROL", "SINTROM"),
    "PROBENECID": ("PROBENECID",),
    "ALLOPURINOL": ("ALLOPURINOL",),
    "ASPIRIN": ("ASPIRIN", "ASPIRINE", "ACETYLSALICYLIQUE"),
    "IBUPROFEN": ("IBUPROFEN", "IBUPROFENE"),
    "KETOPROFEN": ("KETOPROFEN", "KETOPROFENE"),
    "DICLOFENAC": ("DICLOFENAC",),
    "NAPROXEN": ("NAPROXEN",),
    "CELECOXIB": ("CELECOXIB",),
    "ETORICOXIB": ("ETORICOXIB",),
    "RAMIPRIL": ("RAMIPRIL",),
    "PERINDOPRIL": ("PERINDOPRIL",),
    "ENALAPRIL": ("ENALAPRIL",),
    "LISINOPRIL": ("LISINOPRIL",),
    "LOSARTAN": ("LOSARTAN",),
    "VALSARTAN": ("VALSARTAN",),
    "CANDESARTAN": ("CANDESARTAN",),
    # Brand names are identity resolution only; they do not imply interaction coverage.
    "RIVAROXABAN": ("RIVAROXABAN", "XARELTO"),
    "APIXABAN": ("APIXABAN", "ELIQUIS"),
}


def resolve_medication_identity(value: str) -> Optional[str]:
    tokens = set(_norm(value).split())
    matches = [
        identity for identity, aliases in _MEDICATION_ALIASES.items()
        if any(set(_norm(alias).split()) <= tokens for alias in aliases)
    ]
    return matches[0] if len(matches) == 1 else None


def _resolved_medications(meds: Iterable[str]) -> set[str]:
    raw = [str(x).strip() for x in (meds or []) if str(x).strip()]
    return {identity for value in raw if (identity := resolve_medication_identity(value))}


def evaluate_bounded_evidence(
    *, dci: str, current_medications: Iterable[str], pregnancy_status: str,
    renal_status: str, hepatic_status: str, medication_allergies: Iterable[str],
    penicillin_allergy_status: str,
) -> EvidenceEvaluation:
    ingredient = canonical_active_ingredient(dci)
    meds = _resolved_medications(current_medications)
    findings, sources = [], []
    # Identity resolution enables bounded findings; it never upgrades domain
    # completeness.
    if ingredient == "AMOXICILLIN":
        sources = [SRC_AMOX_SANDOZ, SRC_AMOX_TEVA]
        if penicillin_allergy_status == "PRESENT":
            findings.append(EvidenceFinding(
                "AMOXICILLIN_PENICILLIN_ALLERGY_CONTRAINDICATION",
                "CONTRAINDICATED", (SRC_AMOX_SANDOZ,),
            ))
        allergies = set(_norm(" ".join(medication_allergies or [])).split())
        if allergies & {"PENICILLIN", "PENICILLINE", "BETALACTAM", "BETALACTAMINE"}:
            findings.append(EvidenceFinding(
                "AMOXICILLIN_BETA_LACTAM_ALLERGY_REQUIRES_REVIEW",
                "REVIEW", (SRC_AMOX_SANDOZ,),
            ))
        if "METHOTREXATE" in meds:
            findings.append(EvidenceFinding(
                "AMOXICILLIN_METHOTREXATE_INTERACTION", "HIGH_RISK",
                (SRC_AMOX_TEVA,),
            ))
        if meds & {"WARFARIN", "ACENOCOUMAROL"}:
            findings.append(EvidenceFinding(
                "AMOXICILLIN_ORAL_ANTICOAGULANT_MONITORING", "MONITOR",
                (SRC_AMOX_SANDOZ, SRC_AMOX_TEVA),
            ))
        if "PROBENECID" in meds:
            findings.append(EvidenceFinding(
                "AMOXICILLIN_PROBENECID_NOT_RECOMMENDED", "AVOID",
                (SRC_AMOX_SANDOZ,),
            ))
        if "ALLOPURINOL" in meds:
            findings.append(EvidenceFinding(
                "AMOXICILLIN_ALLOPURINOL_RASH_RISK", "REVIEW",
                (SRC_AMOX_SANDOZ,),
            ))
        if renal_status == "IMPAIRMENT_REPORTED":
            findings.append(EvidenceFinding(
                "AMOXICILLIN_RENAL_DOSE_REVIEW_REQUIRED", "REVIEW",
                (SRC_AMOX_SANDOZ,),
            ))
        return EvidenceEvaluation(
            ingredient, True, False, False, tuple(findings), tuple(sources)
        )
    if ingredient == "IBUPROFEN":
        sources = [SRC_IBU_BIOGARAN, SRC_IBU_CRISTERS]
        if pregnancy_status == "YES":
            findings.append(EvidenceFinding(
                "IBUPROFEN_PREGNANCY_GESTATIONAL_AGE_REQUIRED", "BLOCK",
                (SRC_IBU_BIOGARAN,),
            ))
        if renal_status == "IMPAIRMENT_REPORTED":
            findings.append(EvidenceFinding(
                "IBUPROFEN_RENAL_IMPAIRMENT_REQUIRES_SEVERITY_REVIEW", "BLOCK",
                (SRC_IBU_BIOGARAN,),
            ))
        if hepatic_status == "IMPAIRMENT_REPORTED":
            findings.append(EvidenceFinding(
                "IBUPROFEN_HEPATIC_IMPAIRMENT_REQUIRES_SEVERITY_REVIEW", "BLOCK",
                (SRC_IBU_BIOGARAN,),
            ))
        if meds & {"WARFARIN", "ACENOCOUMAROL"}:
            findings.append(EvidenceFinding(
                "IBUPROFEN_ORAL_ANTICOAGULANT_BLEEDING_RISK", "HIGH_RISK",
                (SRC_IBU_CRISTERS,),
            ))
        if "ASPIRIN" in meds:
            findings.append(EvidenceFinding(
                "IBUPROFEN_ASPIRIN_ASSOCIATION_NOT_RECOMMENDED", "AVOID",
                (SRC_IBU_BIOGARAN, SRC_IBU_CRISTERS),
            ))
        nsaids = {
            "IBUPROFEN", "KETOPROFEN", "DICLOFENAC", "NAPROXEN",
            "CELECOXIB", "ETORICOXIB",
        }
        if meds & nsaids:
            findings.append(EvidenceFinding(
                "IBUPROFEN_CONCOMITANT_NSAID_AVOID", "AVOID",
                (SRC_IBU_BIOGARAN, SRC_IBU_CRISTERS),
            ))
        ace_arb = {
            "RAMIPRIL", "PERINDOPRIL", "ENALAPRIL", "LISINOPRIL",
            "LOSARTAN", "VALSARTAN", "CANDESARTAN",
        }
        if meds & ace_arb:
            findings.append(EvidenceFinding(
                "IBUPROFEN_ACE_ARB_RENAL_REVIEW", "MONITOR",
                (SRC_IBU_CRISTERS,),
            ))
        return EvidenceEvaluation(
            ingredient, True, False, False, tuple(findings), tuple(sources)
        )
    return EvidenceEvaluation(ingredient, False, False, False, (), ())
