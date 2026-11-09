"""One explicit R13 clinician decision over a certified staged option; NOT R14."""
import datetime as dt
import json
import uuid
from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from backend import models
from backend.services.cephalo_clinical_cas import cas_replace_clinical_json
from backend.schemas.cephalo_evidence import ClinicianValidationEvidence, ValidationAction
from backend.schemas.cephalo_r13_therapeutic_options import R13TreatmentOptionEvidence, R13TreatmentOptionStatus
from backend.services.cephalo_r14_review_receipt import _current_graph, _graph_digest, _require_clinician
from backend.services.cephalo_r11_r13_staging import STAGING_KEY, _json_hash
from backend.services.cephalo_r13_decision_authority import resolve_r13_staging, require_committed_staging_audit
from backend.services.cephalo_r11_r12_attestation import verified_r11r12_attestation
from backend.services.cephalo_r13_therapeutic_safety import R13TherapeuticSnapshot, validate_r13_therapeutic_options

DECISION_ACTION = "CEPH_R13_OPTION_DECIDED"

class R13DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_revision: StrictInt = Field(gt=0)
    expected_staging_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    option_id: str = Field(min_length=1, max_length=255)
    action: Literal["SELECT_OPTION", "REJECT_OPTION"]


def decide_r13_option(*, patient_id, analysis, actor, request: R13DecisionRequest, db):
    actor_id = _require_clinician(actor)
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    graph, revision = _current_graph(analysis)
    if revision != request.expected_revision:
        raise HTTPException(status_code=409, detail="Révision scientifique périmée.")
    staged, r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
    if staged["content_sha256"] != request.expected_staging_sha256:
        raise HTTPException(status_code=409, detail="Staging R13 modifié.")
    # A selection or rejection has to originate from a previous committed stage.
    require_committed_staging_audit(db=db, analysis=analysis, staged=staged, actor=actor)
    if not verified_r11r12_attestation(
        patient_id=patient_id, analysis=analysis,
        tenant_id=actor.get_employer_id(), graph_sha256=_graph_digest(graph),
        revision=revision, staging_sha256=staged["content_sha256"], db=db,
    ):
        raise HTTPException(
            status_code=409, detail="Attestation praticien R11/R12 requise avant R13."
        )
    if r13.option_validations or any(
        item.status in {R13TreatmentOptionStatus.CLINICIAN_SELECTED,
                        R13TreatmentOptionStatus.CLINICIAN_REJECTED}
        for item in r13.options
    ):
        raise HTTPException(status_code=409, detail="Décision R13 déjà enregistrée.")
    option = next((item for item in r13.options if item.option_id == request.option_id), None)
    if option is None:
        raise HTTPException(status_code=404, detail="Option R13 inconnue.")
    if option.status != R13TreatmentOptionStatus.EVALUABLE or option.blocking_gates:
        raise HTTPException(status_code=409, detail="Option R13 non admissible.")
    now = dt.datetime.now(dt.timezone.utc)
    accept = request.action == "SELECT_OPTION"
    validation_id = f"validation:r13:{uuid.uuid4().hex}"
    updated = R13TreatmentOptionEvidence.model_validate({
        **option.model_dump(mode="python"),
        "status": "CLINICIAN_SELECTED" if accept else "CLINICIAN_REJECTED",
        "clinician_id": f"clinician:{actor_id}",
        "clinician_decided_at": now,
        "decision_validation_ref": validation_id,
    })
    validation = ClinicianValidationEvidence(
        validation_id=validation_id, clinician_id=f"clinician:{actor_id}",
        validated_at=now, action=ValidationAction.ACCEPT if accept else ValidationAction.REJECT,
        target_type="treatment_option", target_id=option.option_id,
        before_snapshot_hash=_json_hash(option.model_dump(mode="json")),
        after_snapshot_hash=_json_hash(updated.model_dump(mode="json")),
    )
    options = [updated if x.option_id == option.option_id else x for x in r13.options]
    try:
        validate_r13_therapeutic_options(R13TherapeuticSnapshot(
            r12_snapshot=r13.r12_snapshot, criteria=r13.criteria,
            options=options, option_validations=[validation],
        ))
    except Exception as exc:
        raise HTTPException(status_code=409, detail="R13 décision invalide.") from exc
    if _graph_digest(_current_graph(analysis)[0]) != staged["graph_sha256"]:
        raise HTTPException(status_code=409, detail="Graphe modifié pendant la validation.")

    new_stage = {**staged, "r13": {
        **staged["r13"],
        "options": [x.model_dump(mode="json") for x in options],
        "option_validations": [validation.model_dump(mode="json")],
    }, "clinical_validation_available": False}
    new_stage["content_sha256"] = _json_hash({k:v for k,v in new_stage.items() if k != "content_sha256"})
    cas_replace_clinical_json(
        db=db, analysis=analysis, patient_id=patient_id,
        expected_revision=revision, expected_stage_sha=staged["content_sha256"],
        replacement={**analysis.angles_data, STAGING_KEY: new_stage},
    )
    db.add(models.AuditLog(
        user_id=actor_id, employer_id=actor.get_employer_id(),
        action=DECISION_ACTION, resource_type="CephaloAnalysis",
        resource_id=str(analysis.id), severity="INFO",
        details=json.dumps({
            "patient_id": patient_id, "analysis_id": analysis.id,
            "revision": revision, "graph_sha256": staged["graph_sha256"],
            "staging_before": staged["content_sha256"],
            "staging_after": new_stage["content_sha256"],
            "validation_id": validation_id, "option_id": option.option_id,
            "actor_user_id": actor_id, "action": request.action,
            "timestamp": now.isoformat(), "clinical_validation_available": False,
        }, sort_keys=True, ensure_ascii=True),
    ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "option_id": option.option_id, "action": request.action,
        "validation_id": validation_id, "staging_sha256": new_stage["content_sha256"],
        "analysis_revision": revision,
        "clinical_validation_available": False, "r14_status": "NOT_VALIDATED",
    }
