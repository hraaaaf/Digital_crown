"""Explicit AUTO_VERIFIED fiducial calibration transition.

The endpoint never trusts ruler-like geometry alone. It resolves an exact validated
physical profile, re-runs the objective gate, then persists a new typed evidence
revision atomically. Practitioner confirmation remains optional and distinct.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.cephalo_auto_calibration_gate import (
    AutoCalibrationState,
    evaluate_auto_calibration,
)
from backend.services.cephalo_auto_calibration_transition import (
    AutoCalibrationTransitionError,
    auto_calibration_data_from_decision,
    rebuild_evidence_after_auto_calibration,
)
from backend.services.cephalo_calibration_candidate import (
    CalibrationCandidate,
    CalibrationCandidateError,
)
from backend.services.cephalo_fiducial_profiles import validated_fiducial_profiles
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY
from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine
from backend.utils.access_control import assert_patient_access

router = APIRouter()


class AutoCalibrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)


def _candidate_from_analysis(angles_data: dict[str, Any]) -> CalibrationCandidate:
    raw = angles_data.get("calibration_candidate")
    if not isinstance(raw, dict):
        raise HTTPException(status_code=409, detail="Aucun candidat de calibration détecté")
    try:
        return CalibrationCandidate.from_ticks(
            axis_x_px=raw.get("axis_x_px"),
            tick_positions_y_px=raw.get("tick_positions_y_px") or [],
        )
    except (CalibrationCandidateError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=409, detail="Candidat de calibration persisté invalide") from exc


@router.post("/analyses/{analysis_id}/auto-calibrate")
def auto_calibrate_analysis_with_provenance(
    analysis_id: int,
    req: AutoCalibrationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = (
        db.query(models.CephaloAnalysis)
        .filter(models.CephaloAnalysis.id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)

    existing_angles = analysis.angles_data if isinstance(analysis.angles_data, dict) else {}
    previous_evidence = existing_angles.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(previous_evidence, dict):
        raise HTTPException(
            status_code=409,
            detail="Auto-calibration réservée aux analyses avec graphe de preuve typé",
        )

    candidate = _candidate_from_analysis(existing_angles)
    profile = validated_fiducial_profiles.resolve(
        profile_id=req.profile_id,
        version=req.profile_version,
    )
    if profile is None:
        raise HTTPException(
            status_code=409,
            detail="Profil fiducial physique non validé ou version indisponible",
        )

    decision = evaluate_auto_calibration(candidate, profile=profile)
    if decision.state is not AutoCalibrationState.AUTO_VERIFIED or decision.mm_per_pixel is None:
        raise HTTPException(
            status_code=409,
            detail=f"Calibration automatique non vérifiée: {decision.reason}",
        )

    raw_landmarks = analysis.landmarks_data if isinstance(analysis.landmarks_data, list) else []
    points_dict = {
        item["id"]: (item["x"], item["y"])
        for item in raw_landmarks
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and "x" in item
        and "y" in item
    }
    if not raw_landmarks or len(points_dict) != len(raw_landmarks):
        raise HTTPException(status_code=400, detail="Landmarks persistés invalides pour recalibrage")

    vision_metadata = existing_angles.get("vision_metadata")
    inference_mode = vision_metadata.get("mode_inference") if isinstance(vision_metadata, dict) else None
    calibrated_at = dt.datetime.now(dt.timezone.utc)

    try:
        geometry = cephalo_engine.calculate_metrics(
            points_dict,
            custom_mm_ratio=decision.mm_per_pixel,
        )
        geometry_payload = geometry.model_dump()
        evidence_payload = rebuild_evidence_after_auto_calibration(
            previous_payload=previous_evidence,
            patient_id=analysis.patient_id,
            image_record_id=analysis.image_original_path,
            result=geometry,
            runtime_landmarks=raw_landmarks,
            inference_mode=inference_mode,
            decision=decision,
            calibrated_at=calibrated_at,
        )
        calibration_data = auto_calibration_data_from_decision(decision)
        calibration_data["triggered_by"] = str(current_user.id)
        calibration_data["calibrated_at"] = calibrated_at.isoformat()

        updated_angles = dict(existing_angles)
        for key in ("analysis_metadata", "metrics", "visual_debug"):
            updated_angles[key] = geometry_payload[key]
        updated_angles["calibration_status"] = "auto_verified"
        updated_angles["calibration_decision"] = {
            "state": decision.state.value,
            "reason": decision.reason,
            "profile_id": profile.profile_id,
            "profile_version": profile.version,
            "clinician_confirmed": False,
        }
        updated_angles[EVIDENCE_GRAPH_KEY] = evidence_payload

        analysis.mm_per_pixel = decision.mm_per_pixel
        analysis.is_calibrated = True
        analysis.calibration_data = calibration_data
        analysis.angles_data = updated_angles
        db.commit()
        db.refresh(analysis)
    except HTTPException:
        db.rollback()
        raise
    except (AutoCalibrationTransitionError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Échec de l'auto-calibration") from exc

    return {
        "status": "success",
        "calibration_state": AutoCalibrationState.AUTO_VERIFIED.value,
        "mm_per_pixel": decision.mm_per_pixel,
        "is_calibrated": True,
        "clinician_confirmation_required": False,
        "clinician_confirmation_recommended": True,
        "profile_id": profile.profile_id,
        "profile_version": profile.version,
    }
