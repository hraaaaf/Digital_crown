"""Neo-Ordonnance N4 bounded medication evidence matrix.

Only explicitly encoded, source-backed facts are evaluated. Absence from this matrix
means UNKNOWN/NOT_COVERED, never safe. Source URLs are retained for auditability.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple
import unicodedata

EVIDENCE_VERSION = "2026-09-30.n4-v1"
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
    interaction_complete_for_inputs: bool
    contraindication_complete_for_inputs: bool
    findings: Tuple[EvidenceFinding, ...]
    source_ids: Tuple[str, ...]
    evidence_version: str = EVIDENCE_VERSION

def _norm(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(ch for ch in text if not unicodedata.combining(ch)).upper().split())

def canonical_active_ingredient(dci: str) -> str:
    value = _norm(dci)
    if value in {"AMOXICILLINE", "AMOXICILLIN"}: return "AMOXICILLIN"
    if value in {"IBUPROFENE", "IBUPROFEN"}: return "IBUPROFEN"
    return value

def _has_any(meds: Iterable[str], needles: Iterable[str]) -> bool:
    hay = [_norm(x) for x in meds]
    return any(any(n in item for n in needles) for item in hay)

def evaluate_bounded_evidence(*, dci: str, current_medications: Iterable[str], pregnancy_status: str, renal_status: str, hepatic_status: str, medication_allergies: Iterable[str], penicillin_allergy_status: str) -> EvidenceEvaluation:
    ingredient = canonical_active_ingredient(dci)
    meds = list(current_medications or [])
    findings = []
    sources = []
    if ingredient == "AMOXICILLIN":
        sources = [SRC_AMOX_SANDOZ, SRC_AMOX_TEVA]
        if penicillin_allergy_status == "PRESENT": findings.append(EvidenceFinding("AMOXICILLIN_PENICILLIN_ALLERGY_CONTRAINDICATION", "CONTRAINDICATED", (SRC_AMOX_SANDOZ,)))
        if _has_any(medication_allergies or [], ("PENICILL", "BETA-LACT", "BETALACT")): findings.append(EvidenceFinding("AMOXICILLIN_BETA_LACTAM_ALLERGY_REQUIRES_REVIEW", "REVIEW", (SRC_AMOX_SANDOZ,)))
        if _has_any(meds, ("METHOTREXATE",)): findings.append(EvidenceFinding("AMOXICILLIN_METHOTREXATE_INTERACTION", "HIGH_RISK", (SRC_AMOX_TEVA,)))
        if _has_any(meds, ("WARFARIN", "ACENOCOUMAROL", "SINTROM")): findings.append(EvidenceFinding("AMOXICILLIN_ORAL_ANTICOAGULANT_MONITORING", "MONITOR", (SRC_AMOX_SANDOZ, SRC_AMOX_TEVA)))
        if _has_any(meds, ("PROBENECID",)): findings.append(EvidenceFinding("AMOXICILLIN_PROBENECID_NOT_RECOMMENDED", "AVOID", (SRC_AMOX_SANDOZ,)))
        if _has_any(meds, ("ALLOPURINOL",)): findings.append(EvidenceFinding("AMOXICILLIN_ALLOPURINOL_RASH_RISK", "REVIEW", (SRC_AMOX_SANDOZ,)))
        if renal_status == "IMPAIRMENT_REPORTED": findings.append(EvidenceFinding("AMOXICILLIN_RENAL_DOSE_REVIEW_REQUIRED", "REVIEW", (SRC_AMOX_SANDOZ,)))
        return EvidenceEvaluation(ingredient, True, True, True, tuple(findings), tuple(sources))
    if ingredient == "IBUPROFEN":
        sources = [SRC_IBU_BIOGARAN, SRC_IBU_CRISTERS]
        if pregnancy_status == "YES": findings.append(EvidenceFinding("IBUPROFEN_PREGNANCY_GESTATIONAL_AGE_REQUIRED", "BLOCK", (SRC_IBU_BIOGARAN,)))
        if renal_status == "IMPAIRMENT_REPORTED": findings.append(EvidenceFinding("IBUPROFEN_RENAL_IMPAIRMENT_REQUIRES_SEVERITY_REVIEW", "BLOCK", (SRC_IBU_BIOGARAN,)))
        if hepatic_status == "IMPAIRMENT_REPORTED": findings.append(EvidenceFinding("IBUPROFEN_HEPATIC_IMPAIRMENT_REQUIRES_SEVERITY_REVIEW", "BLOCK", (SRC_IBU_BIOGARAN,)))
        if _has_any(meds, ("WARFARIN", "ACENOCOUMAROL", "SINTROM")): findings.append(EvidenceFinding("IBUPROFEN_ORAL_ANTICOAGULANT_BLEEDING_RISK", "HIGH_RISK", (SRC_IBU_CRISTERS,)))
        if _has_any(meds, ("ASPIRIN", "ACETYLSALICYL")): findings.append(EvidenceFinding("IBUPROFEN_ASPIRIN_ASSOCIATION_NOT_RECOMMENDED", "AVOID", (SRC_IBU_BIOGARAN, SRC_IBU_CRISTERS)))
        if _has_any(meds, ("IBUPROFEN", "KETOPROFEN", "DICLOFENAC", "NAPROXEN", "CELECOXIB", "ETORICOXIB")): findings.append(EvidenceFinding("IBUPROFEN_CONCOMITANT_NSAID_AVOID", "AVOID", (SRC_IBU_BIOGARAN, SRC_IBU_CRISTERS)))
        if _has_any(meds, ("RAMIPRIL", "PERINDOPRIL", "ENALAPRIL", "LISINOPRIL", "LOSARTAN", "VALSARTAN", "CANDESARTAN")): findings.append(EvidenceFinding("IBUPROFEN_ACE_ARB_RENAL_REVIEW", "MONITOR", (SRC_IBU_CRISTERS,)))
        return EvidenceEvaluation(ingredient, True, True, True, tuple(findings), tuple(sources))
    return EvidenceEvaluation(ingredient, False, False, False, (), ())
