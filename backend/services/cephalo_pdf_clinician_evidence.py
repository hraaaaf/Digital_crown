"""Clinician-audited evidence selected from the persisted cephalometric case.

This is a read-only projection. It never accepts legacy VM clinical_data or AI
narratives, never asserts that the A4 document itself has been signed, and
never converts an evaluable treatment option into a selected treatment.
"""
from __future__ import annotations

from backend.schemas.cephalo_evidence import (
    ReviewState,
    TreatmentOptionStatus,
    ValidationAction,
)
from backend.services.cephalo_evidence_case_integrity import validate_case_evidence_graph
from backend.services.cephalo_evidence_graph import EvidenceGraphSnapshot

CLINICIAN_PDF_EVIDENCE_VERSION = "CEPHALO_CLINICIAN_PDF_EVIDENCE_V1"
_ACCEPT = {ValidationAction.ACCEPT, ValidationAction.EDIT}
_CONFIRMED = {ReviewState.ACCEPTED, ReviewState.EDITED}


def project_audited_clinician_evidence(
    graph: EvidenceGraphSnapshot, *, patient_id: int, case_id: str,
    analysis_id: int, revision: int,
) -> dict:
    """Fail closed on cross-case data, missing audit or conflicting evidence.

    The source graph is the same typed snapshot persisted in angles_data and
    must satisfy case-level graph integrity before any narrative is returned.
    """
    if (
        type(patient_id) is not int or patient_id <= 0
        or not isinstance(case_id, str) or not case_id.strip()
        or type(analysis_id) is not int or analysis_id <= 0
        or type(revision) is not int or revision <= 0
    ):
        raise ValueError("Selected clinical case/revision is not verified")

    validate_case_evidence_graph(graph, patient_id=patient_id, case_id=case_id)
    validations = {
        (item.target_type, item.target_id, item.clinician_id, item.validated_at)
        for item in graph.validations if item.action in _ACCEPT
    }
    diagnoses = [
        item for item in graph.diagnoses
        if item.state in _CONFIRMED
        and not (item.missing_data_refs or item.contradictions or item.opposing_finding_refs)
        and ("diagnosis", item.diagnosis_id, item.clinician_id, item.clinician_validated_at)
        in validations
    ]
    confirmed_ids = {item.diagnosis_id for item in diagnoses}
    diagnostic_lines = [
        {"statement": item.statement[:1500], "validated_at": item.clinician_validated_at.isoformat()}
        for item in diagnoses
    ]

    # Ambiguous multiple purported final plans cannot be resolved by "latest".
    # The report remains draft even when an audited plan is found.
    approved_plan = None
    if len(graph.final_plans) == 1:
        plan = graph.final_plans[0]
        selected_options = {
            option.option_id: option for option in graph.treatment_options
        }
        option = selected_options.get(plan.selected_option_ref)
        plan_audit = ("final_plan", plan.plan_id, plan.clinician_id, plan.clinician_validated_at)
        option_audit = (
            "treatment_option", plan.selected_option_ref,
            plan.clinician_id, option.clinician_selected_at if option else None,
        )
        if (
            option is not None
            and option.status == TreatmentOptionStatus.CLINICIAN_SELECTED
            and not option.missing_gates
            and plan_audit in validations
            and option_audit in validations
            and set(plan.validated_diagnosis_refs).issubset(confirmed_ids)
        ):
            objective_by_id = {item.objective_id: item for item in graph.objectives}
            objective_list = [
                objective_by_id[oid] for oid in plan.validated_objective_refs
                if oid in objective_by_id
                and objective_by_id[oid].state in _CONFIRMED
                and ("objective", oid, objective_by_id[oid].clinician_id,
                     objective_by_id[oid].clinician_validated_at) in validations
            ]
            if len(objective_list) == len(plan.validated_objective_refs):
                approved_plan = {
                    "option_context": {
                        "benefits": [str(v)[:500] for v in option.benefits[:8]],
                        "limits": [str(v)[:500] for v in option.limits[:8]],
                        "risks": [str(v)[:500] for v in option.risks[:8]],
                    },
                    "objectives": [
                        {"target": obj.target[:1000],
                         "success_criterion": obj.success_criterion[:1000]}
                        for obj in objective_list
                    ],
                    "phases": [
                        {
                            "title": phase.title[:600],
                            "procedures": [str(v)[:500] for v in phase.procedures[:8]],
                            "mechanics_or_appliances": [
                                str(v)[:500] for v in phase.mechanics_or_appliances[:8]
                            ],
                            "monitoring": [str(v)[:500] for v in phase.monitoring[:8]],
                            "reassessment_criteria": [
                                str(v)[:500] for v in phase.reassessment_criteria[:8]
                            ],
                        }
                        for phase in plan.phases[:12]
                    ],
                    "retention": [str(v)[:500] for v in plan.retention[:8]],
                    "reassessment_points": [
                        str(v)[:500] for v in plan.reassessment_points[:8]
                    ],
                    "validated_at": plan.clinician_validated_at.isoformat(),
                }

    return {
        "version": CLINICIAN_PDF_EVIDENCE_VERSION,
        "patient_id": patient_id,
        "analysis_id": analysis_id,
        "analysis_revision": revision,
        "diagnoses": diagnostic_lines,
        "plan": approved_plan,
        "report_signed": False,
    }
