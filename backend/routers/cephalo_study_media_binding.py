"""DC-DOS-05 FUE-only HTTP surface; NOT registered in application routers.

A separate approved schema migration and clinical/release decision is necessary
before this module may ever be mounted outside synthetic isolated tests.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission, has_permission
from backend.services.cephalo_study_media_binding import (
    StudyMediaBindingError, bind_study_original_media, read_verified_study_media,
)
from backend.utils.access_control import assert_patient_access

router = APIRouter()


class BindingRequest(BaseModel):
    patient_id: int = Field(gt=0)
    asset_id: int = Field(gt=0)
    expected_revision: int = Field(gt=0)


def _require_isolated_fue(user):
    if (
        os.environ.get("ENVIRONMENT") != "test"
        or os.environ.get("DIGITALCROWN_ISOLATED_RUNTIME", "").lower() not in {"1","true"}
        or os.environ.get("DC_DOS05_FUE_ONLY") != "1"
    ):
        raise HTTPException(status_code=503, detail="DC-DOS-05 is not deployed")
    if not has_permission(user, "patients"):
        raise HTTPException(status_code=403, detail="Patient permission required")


@router.post("/analyses/{study_id}/media-bindings/{role}", status_code=201)
def bind_study_media(
    study_id: int, role: str, body: BindingRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    _require_isolated_fue(current_user)
    assert_patient_access(body.patient_id, current_user, db)
    try:
        binding, created = bind_study_original_media(
            db, employer_id=int(current_user.get_employer_id()),
            patient_id=body.patient_id, study_id=study_id, asset_id=body.asset_id,
            role=role, expected_revision=body.expected_revision,
            created_by=current_user.id,
        )
        db.commit()
        return {
            "id": binding.id, "study_id": binding.study_id,
            "patient_id": binding.patient_id, "asset_id": binding.asset_id,
            "role": binding.role, "asset_sha256": binding.asset_sha256,
            "revision": binding.revision, "created": created,
            "clinical_release": False,
            "cephalo_computation_from_source_proven": False,
        }
    except StudyMediaBindingError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrent write-once binding collision") from exc


@router.get("/analyses/{study_id}/media-bindings")
def get_study_media(
    study_id: int, patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    _require_isolated_fue(current_user)
    assert_patient_access(patient_id, current_user, db)
    try:
        return read_verified_study_media(
            db, employer_id=int(current_user.get_employer_id()),
            patient_id=patient_id, study_id=study_id,
        )
    except StudyMediaBindingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
