"""R15 clinician-facing projection of the certified R11-R14 authority chain.

This module is deliberately presentation-only. It never invents a diagnostic,
problem, objective, treatment option or final strategy. In the absence of a
persisted authoritative clinical snapshot it projects explicit blockers and
keeps clinician validation unavailable.
"""
from __future__ import annotations

from typing import Any, Mapping

from backend.services.cephalo_diagnostic_rule_registry import registry as diagnostic_registry
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_therapeutic_rule_registry import registry as therapeutic_registry
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY

R15_STUDIO_CONTRACT_VERSION = "R15_CLINICAL_STUDIO_VIEW_V1"


def _stage(
    stage_id: str,
    title: str,
    summary: str,
    blockers: list[str],
    provenance: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "title": title,
        "presentation_state": "BLOCKED" if blockers else "AWAITING_CLINICIAN",
        "authoritative_status": None,
        "summary": summary,
        "blocking_gates": blockers,
        "missing_data_refs": [],
        "contradictions": [],
        "contraindications": [],
        "provenance": provenance,
        "clinician_action": {
            "available": False,
            "audit_required": True,
            "label": "Validation praticien",
            "reason": (
                "Action indisponible tant qu'un snapshot clinique autoritaire et sa preuve "
                "traçable ne sont pas résolus par le backend."
            ),
        },
    }


def build_r15_clinical_studio_snapshot(
    *,
    patient_id: int,
    analysis_id: int | None,
    angles_data: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project the current clinical-authority readiness without creating clinical content."""
    payload = dict(angles_data or {})
    graph_present = isinstance(payload.get(EVIDENCE_GRAPH_KEY), dict)
    active_chain_verified = False
    measurement_count = 0
    runtime_blockers: list[str] = []

    if analysis_id is None:
        runtime_blockers.append("cephalo_analysis_missing")
    elif not graph_present:
        runtime_blockers.append("typed_evidence_graph_missing")
    else:
        try:
            projected = project_runtime_chain_read_path(payload, patient_id=patient_id)
            scientific = projected.get("scientific_read_path", {})
            active_chain_verified = scientific.get("active_chain") == "VERIFIED"
            measurement_count = int(scientific.get("current_measurement_count", 0) or 0)
            if not active_chain_verified:
                runtime_blockers.append("active_runtime_chain_unverified")
        except Exception:
            runtime_blockers.append("active_runtime_chain_incoherent")

    diagnostic_rules = len(diagnostic_registry.diagnostic_rules)
    finding_rules = len(diagnostic_registry.finding_rules)
    therapeutic_options = len(therapeutic_registry.option_rules)
    therapeutic_criteria = len(therapeutic_registry.criterion_rules)

    r11_blockers = list(runtime_blockers)
    if diagnostic_rules == 0 or finding_rules == 0:
        r11_blockers.append("diagnostic_rule_registry_empty")
    r11_blockers.append("r11_authoritative_snapshot_not_persisted")

    r12_blockers = ["r11_not_authoritative", "r12_authoritative_snapshot_not_persisted"]

    r13_blockers = ["r12_not_authoritative"]
    if therapeutic_options == 0 or therapeutic_criteria == 0:
        r13_blockers.append("therapeutic_rule_registry_empty")
    r13_blockers.append("r13_authoritative_snapshot_not_persisted")

    r14_blockers = [
        "r13_no_clinician_selected_option",
        "r14_authoritative_snapshot_not_persisted",
    ]

    stages = [
        _stage(
            "R11",
            "Diagnostic scientifique",
            "Aucun diagnostic n'est promu depuis les mesures sans règle source-lockée et snapshot R11 autoritaire.",
            r11_blockers,
            [
                {"label": "Analyse céphalométrique", "value": str(analysis_id) if analysis_id is not None else "absente"},
                {"label": "Chaîne active", "value": "vérifiée" if active_chain_verified else "non vérifiée"},
                {"label": "Mesures typées actives", "value": str(measurement_count)},
                {"label": "Règles diagnostiques actives", "value": str(diagnostic_rules)},
            ],
        ),
        _stage(
            "R12",
            "Problem list & objectifs",
            "Les problèmes et objectifs ne peuvent dériver que d'éléments R11 explicitement validés.",
            r12_blockers,
            [{"label": "Autorité amont", "value": "R11 requis"}],
        ),
        _stage(
            "R13",
            "Options thérapeutiques",
            "Évaluable n'est jamais une prescription. Aucune option n'est auto-sélectionnée.",
            r13_blockers,
            [
                {"label": "Règles d'option actives", "value": str(therapeutic_options)},
                {"label": "Règles de critère actives", "value": str(therapeutic_criteria)},
            ],
        ),
        _stage(
            "R14",
            "Validation clinique finale",
            "Une validation finale exige une option R13 sélectionnée et une preuve praticien résolue, horodatée et traçable.",
            r14_blockers,
            [{"label": "Autorité amont", "value": "R13 sélection praticien requise"}],
        ),
    ]

    unique_blockers = sorted({gate for stage in stages for gate in stage["blocking_gates"]})
    return {
        "contract_version": R15_STUDIO_CONTRACT_VERSION,
        "patient_id": patient_id,
        "analysis_id": analysis_id,
        "evidence_graph_present": graph_present,
        "active_runtime_chain_verified": active_chain_verified,
        "blocking_gate_count": len(unique_blockers),
        "blocking_gates": unique_blockers,
        "stages": stages,
        "clinical_validation_available": False,
        "clinical_validation_reason": (
            "Aucune validation clinique R14 n'est exposée sans snapshot autoritaire persistant et preuve praticien backend."
        ),
    }
