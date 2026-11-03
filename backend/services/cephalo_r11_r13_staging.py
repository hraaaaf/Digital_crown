"""Draft-only R11→R13 cephalometric evidence persistence.

No rule activation, no R13 option selection, no R14 signature, no PDF promotion.
The patient's existing scientific graph is always the authoritative source.
The staged content lives on that *same* local CephaloAnalysis, not in a
cross-patient audit log or a remote service.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy.orm import Session

from backend import models
from backend.schemas.cephalo_evidence import ReviewState
from backend.schemas.cephalo_r12_problem_objectives import R12ObjectiveEvidence, R12ProblemListItem
from backend.schemas.cephalo_r13_therapeutic_options import (
    R13TreatmentOptionEvidence, R13TreatmentOptionStatus, R13TherapeuticCriterionEvidence,
)
from backend.services.cephalo_r14_review_receipt import _current_graph, _graph_digest, _require_clinician
from backend.services.cephalo_r12_problem_objectives_safety import R12ProblemObjectiveSnapshot
from backend.services.cephalo_r13_therapeutic_safety import R13TherapeuticSnapshot, validate_r13_therapeutic_options
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_typed_read import deserialize_evidence_snapshot

STAGING_KEY = "_cephalo_clinical_staging_v1"
STAGING_CONTRACT = "CEPH_R11_R13_STAGING_V1"
STAGING_AUDIT_ACTION = "CEPH_R11_R13_STAGING_SAVED"
STAGING_STATE = "SOURCE_VALIDATED_NON_FINAL"


class R11R13StagingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    expected_revision: StrictInt = Field(gt=0)
    action: Literal["STAGE_R11_R13"]
    problems: list[R12ProblemListItem] = Field(min_length=1)
    objectives: list[R12ObjectiveEvidence] = Field(min_length=1)
    criteria: list[R13TherapeuticCriterionEvidence] = Field(min_length=1)
    options: list[R13TreatmentOptionEvidence] = Field(min_length=1)


def _json_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _clinician_claims_bound(body: R11R13StagingRequest, actor_id: int) -> bool:
    expected = f"clinician:{actor_id}"
    decided = {ReviewState.ACCEPTED, ReviewState.EDITED}
    for item in [*body.problems, *body.objectives]:
        if item.state not in decided or item.clinician_id != expected:
            return False
    for option in body.options:
        if option.status not in {R13TreatmentOptionStatus.BLOCKED, R13TreatmentOptionStatus.EVALUABLE}:
            return False
        if option.clinician_id or option.decision_validation_ref or option.clinician_decided_at:
            return False
    return True


def stage_clinical_evidence(
    *,
    patient_id: int,
    analysis: models.CephaloAnalysis,
    actor: models.User,
    body: R11R13StagingRequest,
    db: Session,
) -> dict[str, Any]:
    """Persist only validated, non-final R11–R13 content in study-local JSON."""
    actor_id = _require_clinician(actor)
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    graph_payload, revision = _current_graph(analysis)
    if body.expected_revision != revision:
        raise HTTPException(status_code=409, detail="Révision scientifique périmée.")
    if not _clinician_claims_bound(body, actor_id):
        raise HTTPException(status_code=403, detail="Auteurs ou décisions R11-R13 non autorisés.")

    # R11 graph MUST be backend-persisted, never taken from a client request.
    try:
        read = project_runtime_chain_read_path(analysis.angles_data, patient_id=patient_id)
        if read.get("scientific_read_path", {}).get("active_chain") != "VERIFIED":
            raise ValueError("active runtime scientific chain not verified")
        graph = deserialize_evidence_snapshot(graph_payload)
        if not graph.findings or not graph.diagnoses:
            raise ValueError("R11 source-locked findings and diagnoses absent")
        if any(src.patient_id != patient_id for src in graph.sources):
            raise ValueError("R11 clinical evidence crosses patient boundary")

        r12 = R12ProblemObjectiveSnapshot(
            diagnostic_graph=graph,
            problems=body.problems,
            objectives=body.objectives,
        )
        r13 = R13TherapeuticSnapshot(
            r12_snapshot=r12,
            criteria=body.criteria,
            options=body.options,
            option_validations=(),
        )
        # Genuine production registries: intentionally empty until approved.
        # The validator reexecutes all R12 and R11 lineage and sources.
        validate_r13_therapeutic_options(r13)
        graph_sha256 = _graph_digest(graph_payload)
    except Exception as exc:
        raise HTTPException(
            status_code=409, detail="Lignée R11→R13 source-lockée non vérifiée."
        ) from exc

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    content = {
        "contract": STAGING_CONTRACT,
        "state": STAGING_STATE,
        "clinical_validation_available": False,
        "patient_id": patient_id,
        "analysis_id": analysis.id,
        "analysis_revision": revision,
        "graph_sha256": graph_sha256,
        "actor_user_id": actor_id,
        "recorded_at": now,
        "r12": {
            "problems": [v.model_dump(mode="json") for v in body.problems],
            "objectives": [v.model_dump(mode="json") for v in body.objectives],
        },
        "r13": {
            "criteria": [v.model_dump(mode="json") for v in body.criteria],
            "options": [v.model_dump(mode="json") for v in body.options],
            "option_validations": [],
        },
    }
    seal = _json_hash(content)
    persisted = {**content, "content_sha256": seal}

    # Recheck the study-bound science before write; no separate client approval.
    current_graph, current_revision = _current_graph(analysis)
    if current_revision != revision or _graph_digest(current_graph) != graph_sha256:
        raise HTTPException(status_code=409, detail="Graphe scientifique modifié pendant la revue.")

    analysis.angles_data = {**analysis.angles_data, STAGING_KEY: persisted}
    db.add(analysis)
    db.add(models.AuditLog(
        user_id=actor_id,
        employer_id=actor.get_employer_id(),
        action=STAGING_AUDIT_ACTION,
        resource_type="CephaloAnalysis",
        resource_id=str(analysis.id),
        severity="INFO",
        details=json.dumps({
            "contract": STAGING_CONTRACT,
            "patient_id": patient_id, "analysis_id": analysis.id,
            "analysis_revision": revision, "graph_sha256": graph_sha256,
            "content_sha256": seal, "actor_user_id": actor_id,
            "recorded_at": now, "clinical_validation_available": False,
        }, sort_keys=True, ensure_ascii=True),
    ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "state": STAGING_STATE,
        "analysis_revision": revision,
        "graph_sha256": graph_sha256,
        "content_sha256": seal,
        "clinical_validation_available": False,
    }


def read_staged_clinical_evidence(
    *, patient_id: int, analysis: models.CephaloAnalysis,
) -> dict[str, Any]:
    if analysis.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Analyse hors patient.")
    payload = analysis.angles_data if isinstance(analysis.angles_data, dict) else {}
    saved = payload.get(STAGING_KEY)
    if not isinstance(saved, dict):
        return {"state": "NOT_STAGED", "clinical_validation_available": False}
    content = {k: v for k, v in saved.items() if k != "content_sha256"}
    current = "STALE"
    try:
        graph, revision = _current_graph(analysis)
        if (
            saved.get("contract") == STAGING_CONTRACT
            and saved.get("state") == STAGING_STATE
            and saved.get("clinical_validation_available") is False
            and saved.get("patient_id") == patient_id
            and saved.get("analysis_id") == analysis.id
            and type(saved.get("analysis_revision")) is int
            and revision == saved["analysis_revision"]
            and saved.get("graph_sha256") == _graph_digest(graph)
            and saved.get("content_sha256") == _json_hash(content)
        ):
            current = "CURRENT_NON_FINAL"
    except (HTTPException, TypeError, ValueError, OverflowError):
        pass
    return {
        "state": current,
        "analysis_revision": saved.get("analysis_revision"),
        "content_sha256": saved.get("content_sha256"),
        "clinical_validation_available": False,
    }
