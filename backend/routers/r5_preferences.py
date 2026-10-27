"""LOT07 R5/07-D: DEV-only, database-persisted, nonclinical UI preferences.

The server does NOT trust client-provided tenant/user/station IDs. No patient data,
bearer tokens or mutable module permissions are accepted. Cookie workstation scope
and authenticated user are resolved independently on every request.
"""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.config import settings
from backend.routers.auth import get_current_user
from backend.routers.workstation_mode import _find_workstation
from backend.routers.workstation_mode import _employer_id, _add_audit_entry

router = APIRouter()
get_db = database.get_db
MODULES = {"dossier","agenda","imagerie","galerie","cephalo","photos","traitement","suivi","documents","presentation"}
GEOMETRIES = {"single":1,"two-columns":2,"two-rows":2,"three-columns":3,"hero-two":3,"grid-2x2":4,"focus-rail":3}
PRESET_DEFINITIONS = {
    "vue-ensemble": ("hero-two", ("dossier","agenda","imagerie")),
    "consultation": ("two-columns", ("dossier","agenda")),
    "agenda-cabinet": ("two-columns", ("agenda","dossier")),
    "imagerie": ("two-columns", ("imagerie","galerie")),
    "comparaison-orthodontique": ("three-columns", ("cephalo","cephalo","photos")),
    "planification-traitements": ("hero-two", ("traitement","dossier","imagerie")),
    "suivi-clinique": ("two-rows", ("suivi","photos")),
    "gestion-administrative": ("two-columns", ("agenda","documents")),
    "presentation-patient": ("single", ("presentation",)),
}

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

class SlotPreference(Strict):
    id: str = Field(pattern=r"^slot-[1-4]$",max_length=6)
    module: Literal["dossier","agenda","imagerie","galerie","cephalo","photos","traitement","suivi","documents","presentation"]

class LayoutPreference(Strict):
    version: Literal[1]
    userId: str = Field(min_length=1,max_length=40)
    workstationId: str = Field(min_length=1,max_length=36)
    id: str = Field(pattern=r"^[a-z0-9-]{1,60}$")
    geometry: Literal["single","two-columns","two-rows","three-columns","hero-two","grid-2x2","focus-rail"]
    slots: list[SlotPreference] = Field(min_length=1,max_length=4)
    ratio: int = Field(ge=37,le=63)

class PreferencePayload(Strict):
    version: Literal[1]
    tenantId: str = Field(min_length=1,max_length=40)
    userId: str = Field(min_length=1,max_length=40)
    workstationId: str = Field(min_length=1,max_length=36)
    signature: Literal["core","iconic"]
    layout: Optional[LayoutPreference]

class PutPreference(Strict):
    expectedRevision: int = Field(ge=0)
    record: PreferencePayload

class UndoPreference(Strict):
    expectedRevision: int = Field(ge=1)

def _scope(request: Request, db: Session, user: models.User) -> models.WorkstationMode:
    if str(getattr(settings,"ENVIRONMENT","")).lower() not in {"development","test"}:
        raise HTTPException(status_code=404,detail="R5 development lab unavailable")
    if not getattr(user,"is_active",False):
        raise HTTPException(status_code=403,detail="Account inactive")
    row = _find_workstation(request,db,_employer_id(user))
    if row is None or row.revoked_at is not None:
        raise HTTPException(status_code=423,detail="VERIFIED_WORKSTATION_REQUIRED")
    if row.default_experience not in (None,"cabinet"):
        raise HTTPException(status_code=423,detail="CABINET_WORKSTATION_REQUIRED")
    return row

def _validate_payload(record: PreferencePayload, user: models.User, row: models.WorkstationMode) -> dict:
    if (record.tenantId != str(_employer_id(user)) or record.userId != str(user.id)
            or record.workstationId != row.id):
        raise HTTPException(status_code=403,detail="SCOPE_MISMATCH")
    data=record.model_dump()
    layout=record.layout
    if layout is not None:
        if layout.userId != str(user.id) or layout.workstationId != row.id:
            raise HTTPException(status_code=403,detail="LAYOUT_SCOPE_MISMATCH")
        modules=[s.module for s in layout.slots]
        if len(modules) != GEOMETRIES[layout.geometry] or [s.id for s in layout.slots] != [
            f"slot-{i+1}" for i in range(len(modules))
        ]:
            raise HTTPException(status_code=422,detail="INVALID_LAYOUT_SLOTS")
        if len(set(modules)) != len(modules):
            # Only real independently-mounted duplicate Céphalo will be certified later.
            raise HTTPException(status_code=422,detail="DUPLICATE_MODULE")
        preset=PRESET_DEFINITIONS.get(layout.id)
        expected_id=f"custom-{layout.geometry}-" + "-".join(modules)
        if preset is None:
            if layout.id != expected_id:
                raise HTTPException(status_code=422,detail="INVALID_LAYOUT_ID")
        elif preset != (layout.geometry,tuple(modules)):
            raise HTTPException(status_code=422,detail="PRESET_MISMATCH")
    return data

def _record(db: Session, user: models.User, station: models.WorkstationMode):
    return db.query(models.R5DesktopPreference).filter(
        models.R5DesktopPreference.employer_id == _employer_id(user),
        models.R5DesktopPreference.user_id == user.id,
        models.R5DesktopPreference.workstation_id == station.id,
    ).first()

def _reply(row):
    return {"revision":row.revision if row else 0,"record":row.payload if row else None,
            "canRollback":bool(row and row.previous_payload)}

@router.get("")
def read_preference(request: Request, db: Session = Depends(get_db),
                    current_user: models.User = Depends(get_current_user)):
    station=_scope(request,db,current_user)
    return _reply(_record(db,current_user,station))

@router.put("")
def put_preference(payload: PutPreference, request: Request, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    station=_scope(request,db,current_user)
    clean=_validate_payload(payload.record,current_user,station)
    old=_record(db,current_user,station)
    revision=old.revision if old else 0
    if payload.expectedRevision != revision:
        raise HTTPException(status_code=409,detail="REVISION_CONFLICT")
    if old:
        old.previous_payload=old.payload
        old.payload=clean
        old.revision+=1
        row=old
    else:
        row=models.R5DesktopPreference(employer_id=_employer_id(current_user),
            user_id=current_user.id,workstation_id=station.id,
            payload=clean,previous_payload=None,revision=1)
        db.add(row)
    _add_audit_entry(db,user=current_user,action="R5_PREF_SAVED",resource_type="R5DesktopPreference",
                     resource_id=station.id,details="Nonclinical preference changed; payload omitted.",
                     request=request)
    db.commit()
    return _reply(row)

@router.post("/rollback")
def rollback_preference(payload: UndoPreference,request: Request,db: Session = Depends(get_db),
                        current_user: models.User = Depends(get_current_user)):
    station=_scope(request,db,current_user)
    row=_record(db,current_user,station)
    if row is None or row.revision != payload.expectedRevision:
        raise HTTPException(status_code=409,detail="REVISION_CONFLICT")
    if row.previous_payload is None:
        raise HTTPException(status_code=409,detail="NO_PREVIOUS_PREFERENCE")
    previous=PreferencePayload.model_validate(row.previous_payload)
    clean=_validate_payload(previous,current_user,station)
    row.previous_payload=row.payload
    row.payload=clean
    row.revision+=1
    _add_audit_entry(db,user=current_user,action="R5_PREF_ROLLBACK",resource_type="R5DesktopPreference",
                     resource_id=station.id,details="Nonclinical preference rollback; payload omitted.",
                     request=request)
    db.commit()
    return _reply(row)
