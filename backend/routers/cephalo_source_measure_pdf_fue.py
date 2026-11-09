"""DC-DOS-06 NONCLINICAL FUE-only PDF. Never mounted in production."""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission, has_permission
from backend.services.cephalo_study_media_binding import StudyMediaBindingError
from backend.services.cephalo_source_measure_pdf_fue import rehearse_source_measure_pdf
from backend.utils.access_control import assert_patient_access

router = APIRouter()


@router.get("/analyses/{study_id}/synthetic-source-measure-pdf")
def synthetic_source_measure_pdf(
    study_id: int,
    patient_id: int = Query(..., gt=0),
    expected_revision: int = Query(..., gt=0),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    if (
        os.environ.get("ENVIRONMENT") != "test"
        or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() not in {"1","true"}
        or os.environ.get("DC_DOS06_FUE_ONLY") != "1"
    ):
        raise HTTPException(status_code=503, detail="DC-DOS-06 is not deployed")
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Patient permission required")
    assert_patient_access(patient_id, current_user, db)
    try:
        content, manifest = rehearse_source_measure_pdf(
            db,
            employer_id=int(current_user.get_employer_id()),
            patient_id=patient_id, study_id=study_id,
            expected_revision=expected_revision,
        )
    except StudyMediaBindingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return Response(
        content=content, media_type="application/pdf", headers={
            "Cache-Control": "private, no-store",
            "Pragma": "no-cache",
            "X-Content-Type-Options": "nosniff",
            "Content-Disposition": "attachment; filename=dc-dos06-synthetic-proof.pdf",
            "X-DC-DOS06-Provenance-SHA256": manifest["provenance_sha256"],
            "X-DC-DOS06-Source-SHA256": manifest["source_sha256"],
            "X-DC-DOS06-Landmark-SHA256": manifest["landmarks_sha256"],
            "X-DC-DOS06-Measurement-SHA256": manifest["measurements_sha256"],
            "X-DC-DOS06-PDF-SHA256": manifest["pdf_sha256"],
            "X-DC-DOS06-Study-Id": str(manifest["study_id"]),
            "X-DC-DOS06-Revision": str(manifest["revision"]),
            "X-Clinical-Release": "false",
            "X-Official-PDF": "false",
        },
    )
