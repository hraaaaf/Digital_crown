"""R14 clinician final decision from a source-locked R13 option.

No client-authored medical strategy, signature, treatment plan, or rule.
Production registries remain empty: genuine R14 approval stays fail-closed.
A successful unit test with synthetic registries is NOT a clinical release.
"""
from __future__ import annotations

import datetime as dt
import json
import uuid
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from backend import models
from backend.schemas.cephalo_evidence import ClinicianValidationEvidence, ValidationAction
from backend.schemas.cephalo_r13_therapeutic_options import R13TreatmentOptionStatus
from backend.schemas.cephalo_r14_final_validation import (
    R14FinalClinicalStatus, R14FinalClinicalStrategyEvidence,
)
from backend.services.cephalo_r11_r13_staging import _json_hash
from backend.services.cephalo_r14_review_receipt import (
    _current_graph, _graph_digest, _require_clinician,
)
from backend.services.cephalo_r13_decision_authority import resolve_r13_staging
from backend.services.cephalo_r13_option_read import read_r13_decision
from backend.services.cephalo_r14_final_validation_safety import (
    R14FinalClinicalSnapshot, validate_r14_final_clinical_validation,
)

R14_KEY = "_cephalo_r14_final_decision_v1"
R14_CONTRACT = "CEPH_R14_FINAL_DECISION_V1"
R14_AUDIT_ACTION = "CEPH_R14_CLINICIAN_FINAL_DECISION"


class R14FinalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: StrictInt = Field(gt=0)
    expected_staging_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    option_id: str = Field(min_length=1, max_length=255)
    action: Literal["VALIDATE_FINAL_R14", "REJECT_FINAL_R14"]


def _strategy_for_option(*, option, r13, identifier, status, actor_id=None,
                         at=None, validation_ref=None):
    criteria = {item.criterion_id: item for item in r13.criteria}
    criterion_ids = [*option.indication_refs, *option.contraindication_refs]
    source_index = {
        (ref.source_id, ref.source_version): ref for ref in option.source_refs
    }
    for criterion_id in criterion_ids:
        criterion = criteria[criterion_id]
        for ref in criterion.source_refs:
            source_index[(ref.source_id, ref.source_version)] = ref

    return R14FinalClinicalStrategyEvidence(
        strategy_id=identifier,
        option_refs=[option.option_id],
        option_validation_refs=[option.decision_validation_ref],
        criterion_refs=criterion_ids,
        source_refs=list(source_index.values()),
        objective_refs=list(option.objective_refs),
        problem_refs=list(option.problem_refs),
        diagnosis_refs=list(option.diagnosis_refs),
        finding_refs=list(option.finding_refs),
        evidence_refs=[option.option_id, *option.evidence_refs],
        missing_data_refs=list(option.missing_data_refs),
        contradictions=list(option.contradictions),
        blocking_gates=[],
        status=status,
        clinician_id=f"clinician:{actor_id}" if actor_id is not None else None,
        clinician_validated_at=at,
        final_validation_ref=validation_ref,
    )


def decide_r14_final(*, patient_id, analysis, actor, request: R14FinalDecisionRequest, db):
    """Explicitly validate/reject only a current and already selected R13 option."""
    actor_id = _require_clinician(actor)
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    graph, revision = _current_graph(analysis)
    if request.expected_revision != revision:
        raise HTTPException(status_code=409, detail="Révision scientifique périmée.")
    staged, r13 = resolve_r13_staging(patient_id=patient_id, analysis=analysis)
    if staged["content_sha256"] != request.expected_staging_sha256:
        raise HTTPException(status_code=409, detail="Preuve thérapeutique modifiée.")
    current = read_r13_decision(
        patient_id=patient_id, analysis=analysis,
        tenant_id=actor.get_employer_id(), db=db,
    )
    if (
        current.get("state") != "CURRENT_R13_DECISION"
        or current.get("action") != "SELECT_OPTION"
        or current.get("option_id") != request.option_id
        or current.get("actor_user_id") != actor_id
    ):
        raise HTTPException(status_code=409, detail="Choix R13 praticien non vérifié.")
    if len(r13.option_validations) != 1:
        raise HTTPException(status_code=409, detail="Validation R13 unique requise.")
    chosen = next((item for item in r13.options if item.option_id == request.option_id), None)
    if (
        chosen is None or chosen.status != R13TreatmentOptionStatus.CLINICIAN_SELECTED
        or chosen.clinician_id != f"clinician:{actor_id}"
        or chosen.blocking_gates or chosen.missing_data_refs or chosen.contradictions
    ):
        raise HTTPException(status_code=409, detail="Option R13 non admissible à R14.")

    existing = analysis.angles_data.get(R14_KEY)
    if isinstance(existing, dict) and existing.get("analysis_revision") == revision:
        raise HTTPException(status_code=409, detail="R14 déjà décidé sur cette révision.")

    stamp = dt.datetime.now(dt.timezone.utc)
    sid = f"strategy:r14:{uuid.uuid4().hex}"
    vid = f"validation:r14:{uuid.uuid4().hex}"
    awaiting = _strategy_for_option(
        option=chosen, r13=r13, identifier=sid,
        status=R14FinalClinicalStatus.AWAITING_CLINICIAN_VALIDATION,
    )
    accepted = request.action == "VALIDATE_FINAL_R14"
    final = _strategy_for_option(
        option=chosen, r13=r13, identifier=sid,
        status=(R14FinalClinicalStatus.CLINICIAN_VALIDATED
                if accepted else R14FinalClinicalStatus.CLINICIAN_REJECTED),
        actor_id=actor_id, at=stamp, validation_ref=vid,
    )
    review = ClinicianValidationEvidence(
        validation_id=vid,
        clinician_id=f"clinician:{actor_id}",
        validated_at=stamp,
        action=ValidationAction.ACCEPT if accepted else ValidationAction.REJECT,
        target_type="final_clinical_strategy",
        target_id=sid,
        before_snapshot_hash=_json_hash(awaiting.model_dump(mode="json")),
        after_snapshot_hash=_json_hash(final.model_dump(mode="json")),
    )
    try:
        # Replays R13 -> R12 -> R11 with the REAL production rule registries.
        # An empty production source registry refuses the positive transition.
        validate_r14_final_clinical_validation(
            R14FinalClinicalSnapshot(
                r13_snapshot=r13, strategies=(final,), final_validations=(review,),
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Autorité scientifique R14 indisponible.") from exc

    current_graph, current_revision = _current_graph(analysis)
    fingerprint = _graph_digest(graph)
    if current_revision != revision or _graph_digest(current_graph) != fingerprint:
        raise HTTPException(status_code=409, detail="Analyse modifiée pendant la revue.")

    now = stamp.isoformat()
    payload = {
        "contract": R14_CONTRACT,
        "patient_id": patient_id,
        "analysis_id": analysis.id,
        "analysis_revision": revision,
        "graph_sha256": fingerprint,
        "r13_staging_sha256": staged["content_sha256"],
        "actor_user_id": actor_id,
        "decided_at": now,
        "decision": request.action,
        "strategy": final.model_dump(mode="json"),
        "validation": review.model_dump(mode="json"),
        # R15/PDF projection is NOT wired to this code. This is not a release.
        "clinical_validation_available": False,
    }
    digest = _json_hash(payload)
    analysis.angles_data = {
        **analysis.angles_data, R14_KEY: {**payload, "content_sha256": digest},
    }
    db.add(analysis)
    db.add(models.AuditLog(
        user_id=actor_id, employer_id=actor.get_employer_id(),
        action=R14_AUDIT_ACTION, resource_type="CephaloAnalysis",
        resource_id=str(analysis.id), severity="INFO",
        details=json.dumps({
            "contract": R14_CONTRACT,
            "patient_id": patient_id, "analysis_id": analysis.id,
            "analysis_revision": revision, "graph_sha256": fingerprint,
            "r13_staging_sha256": staged["content_sha256"],
            "r14_sha256": digest, "actor_user_id": actor_id,
            "decision": request.action, "strategy_id": sid,
            "validation_id": vid, "decided_at": now,
            "clinical_validation_available": False,
        }, sort_keys=True, ensure_ascii=True),
    ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "status": final.status.value, "validation_id": vid,
        "analysis_revision": revision, "r14_sha256": digest,
        "clinical_validation_available": False,
        "pdf_complete": False,
    }
