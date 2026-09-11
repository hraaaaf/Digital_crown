"""Canonical manual-calibration route with typed provenance.

Replaces only POST /analyses/{analysis_id}/calibrate on the IA router.
"""
from __future__ import annotations

import datetime as dt
import math

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import require_permission
from backend.services.cephalo_calibration_evidence import rebuild_evidence_after_manual_calibration
from backend.services.cephalo_runtime_evidence import EVIDENCE_GRAPH_KEY, CephaloRuntimeEvidenceError
from backend.services.cephalo_safe_engine import cephalo_safe_engine as cephalo_engine
from backend.utils.access_control import assert_patient_access

router = APIRouter()


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

    calibrated_at = dt.datetime.now(dt.timezone.utc)
    clinician_id = str(current_user.id)
    calibration_data = {
        "schema_version": "CEPHALO_CALIBRATION_V1",
        "method": "MANUAL_TWO_POINT",
        "method_version": "1",
        "p1": {"x": float(req.p1.x), "y": float(req.p1.y)},
        "p2": {"x": float(req.p2.x), "y": float(req.p2.y)},
        "distance_mm": float(req.distance_mm),
        "mm_per_pixel": float(mm_per_pixel),
        "calibrated_by": clinician_id,
        "calibrated_at": calibrated_at.isoformat(),
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
        # Recompute geometry-dependent compatibility output from the same landmarks
        # and ratio. Practitioner-authored clinical/narrative fields are left intact.
        for key in ("analysis_metadata", "metrics", "visual_debug"):
            updated_angles[key] = geometry_payload[key]
        updated_angles["calibration_status"] = "verified"

        previous_evidence = existing_angles.get(EVIDENCE_GRAPH_KEY)
        if isinstance(previous_evidence, dict):
            updated_angles[EVIDENCE_GRAPH_KEY] = rebuild_evidence_after_manual_calibration(
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
    }


# R1 adds an explicit automatic transition next to the existing manual endpoint.
# Both are mounted under the same canonical IA router and remain distinguishable in
# persisted provenance.
from backend.routers.cephalo_auto_calibration import router as auto_calibration_router
router.include_router(auto_calibration_router)
