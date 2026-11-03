"""Load R13 authority from study-local, source-locked, non-final staging only."""
import json
from fastapi import HTTPException
from backend import models
from backend.schemas.cephalo_evidence import ClinicianValidationEvidence
from backend.schemas.cephalo_r12_problem_objectives import R12ObjectiveEvidence, R12ProblemListItem
from backend.schemas.cephalo_r13_therapeutic_options import (
    R13TherapeuticCriterionEvidence, R13TreatmentOptionEvidence,
)
from backend.services.cephalo_r11_r13_staging import STAGING_KEY, STAGING_CONTRACT, STAGING_AUDIT_ACTION, read_staged_clinical_evidence
from backend.services.cephalo_r14_review_receipt import _current_graph
from backend.services.cephalo_r12_problem_objectives_safety import R12ProblemObjectiveSnapshot
from backend.services.cephalo_r13_therapeutic_safety import R13TherapeuticSnapshot, validate_r13_therapeutic_options
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_typed_read import deserialize_evidence_snapshot


def resolve_r13_staging(*, patient_id: int, analysis: models.CephaloAnalysis):
    status = read_staged_clinical_evidence(patient_id=patient_id, analysis=analysis)
    if status["state"] != "CURRENT_NON_FINAL":
        raise HTTPException(status_code=409, detail="Staging R11–R13 absent ou périmé.")
    saved = analysis.angles_data[STAGING_KEY]
    try:
        runtime = project_runtime_chain_read_path(analysis.angles_data, patient_id=patient_id)
        if runtime.get("scientific_read_path", {}).get("active_chain") != "VERIFIED":
            raise ValueError("Runtime graph not verified")
        graph = deserialize_evidence_snapshot(_current_graph(analysis)[0])
        if not graph.findings or not graph.diagnoses:
            raise ValueError("R11 findings and diagnoses absent")
        if any(source.patient_id != patient_id for source in graph.sources):
            raise ValueError("R11 patient source mismatch")
        r12 = R12ProblemObjectiveSnapshot(
            diagnostic_graph=graph,
            problems=tuple(R12ProblemListItem.model_validate(x) for x in saved["r12"]["problems"]),
            objectives=tuple(R12ObjectiveEvidence.model_validate(x) for x in saved["r12"]["objectives"]),
        )
        r13 = R13TherapeuticSnapshot(
            r12_snapshot=r12,
            criteria=tuple(R13TherapeuticCriterionEvidence.model_validate(x) for x in saved["r13"]["criteria"]),
            options=tuple(R13TreatmentOptionEvidence.model_validate(x) for x in saved["r13"]["options"]),
            option_validations=tuple(ClinicianValidationEvidence.model_validate(x) for x in saved["r13"]["option_validations"]),
        )
        validate_r13_therapeutic_options(r13)
        return saved, r13
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Source R11–R13 non vérifiée.") from exc


def require_committed_staging_audit(*, db, analysis, staged, actor):
    """Tie a stage to the audit committed by the backend authenticated route."""
    audit = (
        db.query(models.AuditLog)
        .filter(
            models.AuditLog.action == STAGING_AUDIT_ACTION,
            models.AuditLog.resource_type == "CephaloAnalysis",
            models.AuditLog.resource_id == str(analysis.id),
            models.AuditLog.employer_id == actor.get_employer_id(),
        )
        .order_by(models.AuditLog.id.desc()).first()
    )
    try:
        claim = json.loads(audit.details) if audit else {}
        if not (
            claim.get("contract") == STAGING_CONTRACT
            and claim.get("patient_id") == analysis.patient_id
            and claim.get("analysis_id") == analysis.id
            and claim.get("analysis_revision") == staged["analysis_revision"]
            and claim.get("graph_sha256") == staged["graph_sha256"]
            and claim.get("content_sha256") == staged["content_sha256"]
            and claim.get("actor_user_id") == audit.user_id == staged["actor_user_id"]
            and claim.get("recorded_at") == staged["recorded_at"]
            and claim.get("clinical_validation_available") is False
        ):
            raise ValueError("Staging audit does not match")
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail="Audit source du staging non vérifié.") from exc
