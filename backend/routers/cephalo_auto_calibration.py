"""Explicit fiducial calibration transitions with distinct automatic/human provenance."""
from __future__ import annotations

import datetime as dt
from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.cephalo_auto_calibration_confirmation import (
    AutoCalibrationConfirmationError,
    confirm_auto_calibration,
)
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
    """Trigger only. Physical profile identity must come from persisted server evidence."""

    model_config = ConfigDict(extra="forbid")


def _load_analysis(analysis_id: int, db: Session, current_user: models.User):
    analysis = (
        db.query(models.CephaloAnalysis)
        .filter(models.CephaloAnalysis.id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)
    return analysis


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


def _bound_profile_from_analysis(angles_data: dict[str, Any]):
    """Resolve only a profile identity already bound to the persisted candidate.

    The request cannot choose a physical profile. A future detector/integration may
    bind one only when it has deterministic evidence for that identity.
    """
    raw = angles_data.get("calibration_candidate")
    if not isinstance(raw, dict):
        raise HTTPException(status_code=409, detail="Aucun candidat de calibration détecté")

    binding = raw.get("profile_binding")
    if not isinstance(binding, Mapping):
        raise HTTPException(
            status_code=409,
            detail="Candidat sans identité fiduciale physique vérifiée",
        )

    profile_id = binding.get("profile_id")
    profile_version = binding.get("profile_version")
    validation_reference = binding.get("validation_reference")
    if (
        not isinstance(profile_id, str)
        or not profile_id.strip()
        or not isinstance(profile_version, str)
        or not profile_version.strip()
        or not isinstance(validation_reference, str)
        or not validation_reference.strip()
    ):
        raise HTTPException(
            status_code=409,
            detail="Liaison du profil fiducial persisté invalide",
        )

    profile = validated_fiducial_profiles.resolve(
        profile_id=profile_id.strip(),
        version=profile_version.strip(),
    )
    if profile is None:
        raise HTTPException(
            status_code=409,
            detail="Profil fiducial physique non validé ou version indisponible",
        )
    if profile.validation_reference != validation_reference.strip():
        raise HTTPException(
            status_code=409,
            detail="Référence physique du candidat incompatible avec le profil validé",
        )
    return profile


@router.post("/analyses/{analysis_id}/auto-calibrate")
def auto_calibrate_analysis_with_provenance(
    analysis_id: int,
    req: AutoCalibrationRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = _load_analysis(analysis_id, db, current_user)
    existing_angles = analysis.angles_data if isinstance(analysis.angles_data, dict) else {}
    previous_evidence = existing_angles.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(previous_evidence, dict):
        raise HTTPException(
            status_code=409,
            detail="Auto-calibration réservée aux analyses avec graphe de preuve typé",
        )

    _ = req  # Explicit trigger body; profile selection is intentionally impossible.
    candidate = _candidate_from_analysis(existing_angles)
    profile = _bound_profile_from_analysis(existing_angles)

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


@router.post("/analyses/{analysis_id}/auto-calibration/confirm")
def confirm_auto_calibration_with_provenance(
    analysis_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Optionally confirm an existing AUTO_VERIFIED result without changing its scale."""
    analysis = _load_analysis(analysis_id, db, current_user)
    if analysis.is_calibrated is not True or analysis.mm_per_pixel is None:
        raise HTTPException(status_code=409, detail="Aucune auto-calibration vérifiée à confirmer")

    calibration_data = analysis.calibration_data
    if not isinstance(calibration_data, Mapping):
        raise HTTPException(status_code=409, detail="Provenance de calibration absente")
    if calibration_data.get("method") != "AUTO_FIDUCIAL_PROFILE":
        raise HTTPException(status_code=409, detail="La calibration courante n'est pas automatique")
    if calibration_data.get("state") != AutoCalibrationState.AUTO_VERIFIED.value:
        raise HTTPException(status_code=409, detail="La calibration automatique n'est pas en état AUTO_VERIFIED")

    existing_angles = analysis.angles_data if isinstance(analysis.angles_data, dict) else {}
    previous_evidence = existing_angles.get(EVIDENCE_GRAPH_KEY)
    if not isinstance(previous_evidence, dict):
        raise HTTPException(status_code=409, detail="Graphe de preuve typé absent")

    confirmed_at = dt.datetime.now(dt.timezone.utc)
    clinician_id = str(current_user.id)
    try:
        evidence_payload = confirm_auto_calibration(
            previous_payload=previous_evidence,
            patient_id=analysis.patient_id,
            clinician_id=clinician_id,
            confirmed_at=confirmed_at,
        )
        updated_calibration_data = dict(calibration_data)
        updated_calibration_data["state"] = AutoCalibrationState.CLINICIAN_CONFIRMED.value
        updated_calibration_data["confirmation"] = {
            "confirmed_by": clinician_id,
            "confirmed_at": confirmed_at.isoformat(),
        }

        updated_angles = dict(existing_angles)
        updated_angles["calibration_status"] = "clinician_confirmed"
        decision = updated_angles.get("calibration_decision")
        updated_decision = dict(decision) if isinstance(decision, Mapping) else {}
        updated_decision["state"] = AutoCalibrationState.CLINICIAN_CONFIRMED.value
        updated_decision["clinician_confirmed"] = True
        updated_decision["confirmed_by"] = clinician_id
        updated_decision["confirmed_at"] = confirmed_at.isoformat()
        updated_angles["calibration_decision"] = updated_decision
        updated_angles[EVIDENCE_GRAPH_KEY] = evidence_payload

        analysis.calibration_data = updated_calibration_data
        analysis.angles_data = updated_angles
        db.commit()
        db.refresh(analysis)
    except AutoCalibrationConfirmationError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Échec de la confirmation de calibration") from exc

    return {
        "status": "success",
        "calibration_state": AutoCalibrationState.CLINICIAN_CONFIRMED.value,
        "mm_per_pixel": analysis.mm_per_pixel,
        "is_calibrated": True,
        "clinician_confirmation_required": False,
        "clinician_confirmation_recommended": False,
        "confirmed_by": clinician_id,
        "confirmed_at": confirmed_at.isoformat(),
    }
