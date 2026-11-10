"""J2.1 FUE-only HTTP adapter; never registered in production router tables.

No clinical scenes can be accessed without a verified JWT, patient permission,
a correct study/media source, and a disposable isolated application test DB.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend import database, models
from backend.routers.auth import has_permission, require_permission
from backend.schemas.cephalo_premium_scene_contract import CephaloPremiumSceneDraft
from backend.services.ceph_premium_scene_app_fue import (
    SceneAppFueError, get_scene, save_scene, assert_isolated_scene_app_db,
)
from backend.utils.access_control import assert_patient_access


router = APIRouter()


class SceneWriteRequest(BaseModel):
    scene: CephaloPremiumSceneDraft
    expected_parent_sha256: str | None = None


def _access(db: Session, current_user, *, patient_id: int):
    try:
        assert_isolated_scene_app_db(db)
    except SceneAppFueError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    if not has_permission(current_user, "patients"):
        raise HTTPException(status_code=403, detail="Patient permission required")
    assert_patient_access(patient_id, current_user, db)


@router.post("/analyses/{study_id}/premium-scene-fue", status_code=201)
def write_scene(study_id: int, body: SceneWriteRequest,
                db: Session = Depends(database.get_db),
                current_user: models.User = Depends(require_permission("cephalo"))):
    _access(db, current_user, patient_id=body.scene.identity.patient_id)
    try:
        response = save_scene(
            db, scene=body.scene, expected_parent_sha256=body.expected_parent_sha256,
            actor_employer_id=int(current_user.get_employer_id()),
            actor_patient_id=body.scene.identity.patient_id,
            actor_study_id=study_id, actor_user_id=current_user.id,
        )
        db.commit()
        return response
    except SceneAppFueError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Scene CAS write collision") from exc


@router.get("/analyses/{study_id}/premium-scene-fue")
def read_scene(study_id: int, patient_id: int,
               db: Session = Depends(database.get_db),
               current_user: models.User = Depends(require_permission("cephalo"))):
    _access(db, current_user, patient_id=patient_id)
    try:
        return get_scene(
            db, actor_employer_id=int(current_user.get_employer_id()),
            actor_patient_id=patient_id, actor_study_id=study_id,
        )
    except SceneAppFueError as exc:
        db.rollback()
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
