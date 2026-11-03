"""Fail-closed read projection of R14 practitioner decision: never PDF authority."""
import json

from fastapi import HTTPException

from backend import models
from backend.schemas.cephalo_evidence import ClinicianValidationEvidence, ValidationAction
from backend.schemas.cephalo_r14_final_validation import (
    R14FinalClinicalStatus, R14FinalClinicalStrategyEvidence,
)
from backend.services.cephalo_r11_r13_staging import _json_hash
from backend.services.cephalo_r13_decision_authority import resolve_r13_staging
from backend.services.cephalo_r13_option_read import read_r13_decision
from backend.services.cephalo_r14_final_decision import (
    R14_KEY, R14_CONTRACT, R14_AUDIT_ACTION, _strategy_for_option,
)
from backend.services.cephalo_r14_final_validation_safety import (
    R14FinalClinicalSnapshot, validate_r14_final_clinical_validation,
)
from backend.services.cephalo_r14_review_receipt import _current_graph, _graph_digest


def read_r14_final(*, patient_id, analysis, tenant_id, db):
    """No source, hash, doctor or audit shortcut is treated as a final signoff."""
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    stored = (
        analysis.angles_data.get(R14_KEY)
        if isinstance(analysis.angles_data, dict) else None
    )
    if not isinstance(stored, dict):
        return {"state": "NOT_DECIDED", "clinical_validation_available": False}
    try:
        body = {key: val for key, val in stored.items() if key != "content_sha256"}
        graph, revision = _current_graph(analysis)
        staged, r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
        choice = read_r13_decision(
            patient_id=patient_id, analysis=analysis, tenant_id=tenant_id, db=db,
        )
        if not (
            stored["contract"] == R14_CONTRACT
            and stored["patient_id"] == patient_id
            and stored["analysis_id"] == analysis.id
            and type(stored["analysis_revision"]) is int
            and stored["analysis_revision"] == revision
            and stored["graph_sha256"] == _graph_digest(graph)
            and stored["r13_staging_sha256"] == staged["content_sha256"]
            and stored["content_sha256"] == _json_hash(body)
            and stored["clinical_validation_available"] is False
            and choice.get("state") == "CURRENT_R13_DECISION"
            and choice.get("action") == "SELECT_OPTION"
        ):
            raise ValueError("Current R14 lineage not established")

        strategy = R14FinalClinicalStrategyEvidence.model_validate(stored["strategy"])
        validation = ClinicianValidationEvidence.model_validate(stored["validation"])
        if not (
            len(strategy.option_refs) == 1
            and strategy.option_refs[0] == choice["option_id"]
            and strategy.clinician_id == f"clinician:{choice['actor_user_id']}"
            and strategy.final_validation_ref == validation.validation_id
            and validation.target_id == strategy.strategy_id
            and validation.target_type == "final_clinical_strategy"
            and stored["actor_user_id"] == choice["actor_user_id"]
            and stored["decided_at"] == validation.validated_at.isoformat()
            and strategy.clinician_validated_at == validation.validated_at
        ):
            raise ValueError("Doctor or strategy mismatch")
        if stored["decision"] == "VALIDATE_FINAL_R14":
            if (strategy.status != R14FinalClinicalStatus.CLINICIAN_VALIDATED
                    or validation.action != ValidationAction.ACCEPT):
                raise ValueError("R14 acceptance mismatch")
        elif stored["decision"] == "REJECT_FINAL_R14":
            if (strategy.status != R14FinalClinicalStatus.CLINICIAN_REJECTED
                    or validation.action != ValidationAction.REJECT):
                raise ValueError("R14 rejection mismatch")
        else:
            raise ValueError("R14 decision action unsupported")

        option = next(x for x in r13.options if x.option_id == choice["option_id"])
        awaiting = _strategy_for_option(
            option=option, r13=r13, identifier=strategy.strategy_id,
            status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
        )
        if (
            validation.before_snapshot_hash != _json_hash(awaiting.model_dump(mode="json"))
            or validation.after_snapshot_hash != _json_hash(strategy.model_dump(mode="json"))
        ):
            raise ValueError("R14 strategy before/after digest mismatch")

        # This reruns REAL production source registries on every read.
        validate_r14_final_clinical_validation(
            R14FinalClinicalSnapshot(
                r13_snapshot=r13, strategies=(strategy,), final_validations=(validation,),
            )
        )
        audit = (
            db.query(models.AuditLog)
            .filter(
                models.AuditLog.action == R14_AUDIT_ACTION,
                models.AuditLog.resource_type == "CephaloAnalysis",
                models.AuditLog.resource_id == str(analysis.id),
                models.AuditLog.employer_id == tenant_id,
            ).order_by(models.AuditLog.id.desc()).first()
        )
        claim = json.loads(audit.details) if audit else {}
        if not (
            claim.get("contract") == R14_CONTRACT
            and claim.get("patient_id") == patient_id
            and claim.get("analysis_id") == analysis.id
            and claim.get("analysis_revision") == revision
            and claim.get("graph_sha256") == stored["graph_sha256"]
            and claim.get("r13_staging_sha256") == staged["content_sha256"]
            and claim.get("r14_sha256") == stored["content_sha256"]
            and claim.get("actor_user_id") == audit.user_id == choice["actor_user_id"]
            and claim.get("decision") == stored["decision"]
            and claim.get("strategy_id") == strategy.strategy_id
            and claim.get("validation_id") == validation.validation_id
            and claim.get("decided_at") == stored["decided_at"]
            and claim.get("clinical_validation_available") is False
        ):
            raise ValueError("Final practitioner decision audit mismatch")
        return {
            "state": "CURRENT_R14_DECISION_NON_RELEASED",
            "status": strategy.status.value,
            "option_id": choice["option_id"],
            "actor_user_id": audit.user_id,
            "analysis_revision": revision,
            "validation_id": validation.validation_id,
            "clinical_validation_available": False,
            "pdf_complete": False,
        }
    except Exception:
        return {"state": "STALE_OR_UNVERIFIED", "clinical_validation_available": False}
