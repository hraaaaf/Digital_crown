"""Read-time R13 decision currency; never grant R14 clinical authority."""
import json
from backend import models
from backend.schemas.cephalo_evidence import ClinicianValidationEvidence, ValidationAction
from backend.services.cephalo_r13_option_decision import DECISION_ACTION
from backend.services.cephalo_r13_decision_authority import resolve_r13_staging
from backend.services.cephalo_r11_r13_staging import STAGING_KEY, read_staged_clinical_evidence


def read_r13_decision(*, patient_id, analysis, tenant_id, db):
    state = read_staged_clinical_evidence(patient_id=patient_id, analysis=analysis)
    if state["state"] != "CURRENT_NON_FINAL":
        return {"state": state["state"], "clinical_validation_available": False}
    try:
        staged, r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
        if len(r13.option_validations) != 1:
            return {"state": "NO_DECISION", "clinical_validation_available": False}
        validation = r13.option_validations[0]
        selected = next(x for x in r13.options if x.decision_validation_ref == validation.validation_id)
        audit = (
            db.query(models.AuditLog)
            .filter(models.AuditLog.action == DECISION_ACTION,
                    models.AuditLog.resource_type == "CephaloAnalysis",
                    models.AuditLog.resource_id == str(analysis.id),
                    models.AuditLog.employer_id == tenant_id)
            .order_by(models.AuditLog.id.desc()).first()
        )
        claim = json.loads(audit.details) if audit else {}
        action = (
            "SELECT_OPTION" if validation.action == ValidationAction.ACCEPT else
            "REJECT_OPTION" if validation.action == ValidationAction.REJECT else None
        )
        if not (
            action is not None
            and claim.get("patient_id") == patient_id
            and claim.get("analysis_id") == analysis.id
            and claim.get("revision") == staged["analysis_revision"]
            and claim.get("graph_sha256") == staged["graph_sha256"]
            and claim.get("staging_after") == staged["content_sha256"]
            and claim.get("validation_id") == validation.validation_id
            and claim.get("option_id") == validation.target_id == selected.option_id
            and claim.get("actor_user_id") == audit.user_id
            and validation.clinician_id == f"clinician:{audit.user_id}"
            and claim.get("timestamp") == validation.validated_at.isoformat()
            and selected.clinician_decided_at == validation.validated_at
            and claim.get("action") == action
            and claim.get("clinical_validation_available") is False
        ):
            raise ValueError("Unverified R13 audit")
        return {
            "state": "CURRENT_R13_DECISION",
            "option_id": selected.option_id,
            "action": action,
            "validation_id": validation.validation_id,
            "actor_user_id": audit.user_id,
            "clinical_validation_available": False,
            "r14_status": "NOT_VALIDATED",
        }
    except (ValueError, TypeError, KeyError, StopIteration, AttributeError, Exception):
        return {"state": "UNVERIFIED", "clinical_validation_available": False}
