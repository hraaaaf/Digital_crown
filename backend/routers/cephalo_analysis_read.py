"""Canonical cephalometric analysis GET with typed scientific read authority."""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend import database, models, schemas
from backend.routers.auth import require_permission
from backend.services.cephalo_runtime_chain import project_runtime_chain_read_path
from backend.services.cephalo_typed_read import CephaloTypedReadError
from backend.utils.access_control import assert_patient_access

router = APIRouter()


@router.get("/analyses/{analysis_id}", response_model=schemas.CephaloAnalysisOut)
def get_analysis_with_typed_read_path(
    analysis_id: int,
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

    out = schemas.CephaloAnalysisOut.model_validate(analysis)
    if isinstance(out.angles_data, dict):
        try:
            out.angles_data = project_runtime_chain_read_path(
                out.angles_data,
                patient_id=analysis.patient_id,
            )
        except CephaloTypedReadError as exc:
            raise HTTPException(
                status_code=409,
                detail="Preuve céphalométrique persistée incohérente; lecture scientifique bloquée.",
            ) from exc

        if "calibration_status" not in out.angles_data:
            out.angles_data = {
                **out.angles_data,
                "calibration_status": "verified" if analysis.is_calibrated else "unverified",
            }
    return out


# R23-G2 experimental reader: separate from the canonical clinical GET.
# No URL/query parameter can turn on the reference ledger in the PDF/clinical path.
@router.get("/analyses/{analysis_id}/r23g2-reference-profiles")
def get_r23g2_reference_profiles(
    analysis_id: int,
    response: Response,
    expected_revision: int = Query(..., ge=1),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    analysis = (
        db.query(models.CephaloAnalysis)
        .filter(models.CephaloAnalysis.id == analysis_id)
        .first()
    )
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    assert_patient_access(analysis.patient_id, current_user, db)

    if not isinstance(analysis.angles_data, dict):
        raise HTTPException(status_code=409, detail="Lecture scientifique de référence bloquée")
    try:
        projected = project_runtime_chain_read_path(
            analysis.angles_data,
            patient_id=analysis.patient_id,
            include_r23g2_reference_profiles=True,
        )
    except CephaloTypedReadError as exc:
        raise HTTPException(status_code=409, detail="Lecture scientifique de référence bloquée") from exc

    scientific = projected.get("scientific_read_path") or {}
    if (scientific.get("authority") != "EVIDENCE_GRAPH_V1"
            or scientific.get("active_chain") != "VERIFIED"
            or type(scientific.get("revision")) is not int
            or scientific["revision"] != expected_revision):
        raise HTTPException(status_code=409, detail="Révision ou preuve de l'étude non vérifiée")

    profiles = scientific.get("r23g2_reference_profiles")
    expected = {"mcnamara": 13, "com": 10, "ricketts_atlas2009": 33, "ricketts_gregoret13": 13}
    if (not isinstance(profiles, dict) or set(profiles) != set(expected)):
        raise HTTPException(status_code=409, detail="Contrat des profils de référence incomplet")
    for name, size in expected.items():
        profile = profiles[name]
        if (not isinstance(profile, dict)
                or profile.get("classification_authority") is not False
                or not isinstance(profile.get("rows"), list)
                or len(profile["rows"]) != size):
            raise HTTPException(status_code=409, detail="Contrat de référence non certifié")
        for row in profile["rows"]:
            if (row.get("classification_authority") is not False
                    or (row.get("availability_status") != "AVAILABLE"
                        and (row.get("value") is not None or row.get("focus_evidence") is not None))):
                raise HTTPException(status_code=409, detail="Preuve de référence invalide")

    response.headers["Cache-Control"] = "no-store"
    return {
        "analysis_id": analysis_id,
        "revision": expected_revision,
        "authority": "EVIDENCE_GRAPH_V1",
        "active_chain": "VERIFIED",
        "clinical_release": False,
        "reference_display_only": True,
        "profiles": profiles,
    }
