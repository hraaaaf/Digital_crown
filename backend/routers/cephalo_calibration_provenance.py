"""Canonical clinician-verified calibration route with typed provenance.

Replaces only POST /analyses/{analysis_id}/calibrate on the IA router.
A persisted ruler candidate is promoted to verified fiducial provenance only when
its detected points are the same points the clinician confirms. Edited points
remain an explicit manual two-point calibration.
"""
from __future__ import annotations

import datetime as dt
import math
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import require_permission
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, CephaloRuntimeEvidenceError
from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine
from backend.utils.access_control import assert_patient_access

router = APIRouter()


def _same_point(candidate: Any, x: float, y: float) -> bool:
    return (
        isinstance(candidate, list)
        and len(candidate) == 2
        and all(isinstance(value, (int, float)) for value in candidate)
        and math.isclose(float(candidate[0]), float(x), rel_tol=0.0, abs_tol=1e-6)
        and math.isclose(float(candidate[1]), float(y), rel_tol=0.0, abs_tol=1e-6)
    )


def _confirmed_ruler_candidate(analysis: models.CephaloAnalysis, req: schemas.CalibrationRequest) -> bool:
    candidate = analysis.calibration_data
    if not isinstance(candidate, dict):
        return False
    if candidate.get("schema_version") != "CEPHALO_CALIBRATION_CANDIDATE_V1":
        return False
    if candidate.get("method") != "RULER_TICK_CANDIDATE_V1":
        return False
    if candidate.get("verification_status") != "UNVERIFIED":
        return False
    return _same_point(candidate.get("p1"), req.p1.x, req.p1.y) and _same_point(
        candidate.get("p2"), req.p2.x, req.p2.y
    )


def _promote_calibration_source(payload: dict[str, Any], *, ruler_candidate: bool) -> dict[str, Any]:
    if not ruler_candidate:
        return payload
    for source in payload.get("sources", []):
        if isinstance(source, dict) and source.get("kind") == "calibration":
            source["quality_status"] = "VERIFIED_RULER_FIDUCIAL"
            metadata = source.get("metadata")
            if isinstance(metadata, dict):
                metadata["method"] = "RULER_TICK_CANDIDATE_V1"
                metadata["method_version"] = "1"
                metadata["clinician_confirmation"] = True
    return payload


@router.post("/analyses/{analysis_id}/calibrate")
def calibrate_analysis_with_provenance(
    analysis_id: int,
    req: schemas.CalibrationRequest,
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

    dist_px = math.hypot(req.p2.x - req.p1.x, req.p2.y - req.p1.y)
    if dist_px < 5:
        raise HTTPException(
            status_code=400,
            detail="Les points de calibration sont trop proches (min 5px)",
        )

    mm_per_pixel = req.distance_mm / dist_px
    if not math.isfinite(mm_per_pixel) or mm_per_pixel < 0.01 or mm_per_pixel > 2.0:
        raise HTTPException(
            status_code=400,
            detail=f"Ratio mm/pixel aberrant ({mm_per_pixel:.4f}). Verifiez vos points.",
        )

    ruler_candidate = _confirmed_ruler_candidate(analysis, req)
    calibrated_at = dt.datetime.now(dt.timezone.utc)
    clinician_id = str(current_user.id)
    method = "RULER_TICK_CANDIDATE_V1" if ruler_candidate else "MANUAL_TWO_POINT"
    quality_status = "VERIFIED_RULER_FIDUCIAL" if ruler_candidate else "VERIFIED_MANUAL_TWO_POINT"
    calibration_data = {
        "schema_version": "CEPHALO_CALIBRATION_V1",
        "method": method,
        "method_version": "1",
        "quality_status": quality_status,
        "p1": {"x": float(req.p1.x), "y": float(req.p1.y)},
        "p2": {"x": float(req.p2.x), "y": float(req.p2.y)},
        "distance_mm": float(req.distance_mm),
        "mm_per_pixel": float(mm_per_pixel),
        "calibrated_by": clinician_id,
        "calibrated_at": calibrated_at.isoformat(),
        "clinician_confirmation": True,
    }

    raw_landmarks = analysis.landmarks_data if isinstance(analysis.landmarks_data, list) else []
    points_dict = {
        item["id"]: (item["x"], item["y"])
        for item in raw_landmarks
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and "x" in item
        and "y" in item
    }
    if len(points_dict) != len(raw_landmarks):
        raise HTTPException(status_code=400, detail="Landmarks persistés invalides pour recalibrage")

    try:
        geometry = cephalo_engine.calculate_metrics(
            points_dict,
            custom_mm_ratio=mm_per_pixel,
        )
        geometry_payload = geometry.model_dump()

        existing_angles = analysis.angles_data if isinstance(analysis.angles_data, dict) else {}
        updated_angles = dict(existing_angles)
        for key in ("analysis_metadata", "metrics", "visual_debug"):
            updated_angles[key] = geometry_payload[key]
        updated_angles["calibration_status"] = "verified"

        previous_evidence = existing_angles.get(EVIDENCE_GRAPH_KEY)
        if isinstance(previous_evidence, dict):
            rebuilt = rebuild_evidence_after_manual_calibration(
                previous_payload=previous_evidence,
                patient_id=analysis.patient_id,
                image_record_id=analysis.image_original_path,
                result=geometry,
                runtime_landmarks=raw_landmarks,
                p1=calibration_data["p1"],
                p2=calibration_data["p2"],
                distance_mm=calibration_data["distance_mm"],
                clinician_id=clinician_id,
                calibrated_at=calibrated_at,
            )
            updated_angles[EVIDENCE_GRAPH_KEY] = _promote_calibration_source(
                rebuilt,
                ruler_candidate=ruler_candidate,
            )

        analysis.mm_per_pixel = mm_per_pixel
        analysis.is_calibrated = True
        analysis.calibration_data = calibration_data
        analysis.angles_data = updated_angles
        db.commit()
        db.refresh(analysis)
    except HTTPException:
        db.rollback()
        raise
    except (CephaloRuntimeEvidenceError, ValueError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Échec du calibrage") from exc

    return {
        "status": "success",
        "mm_per_pixel": mm_per_pixel,
        "is_calibrated": True,
        "calibration_method": method,
        "quality_status": quality_status,
    }
