"""Authenticated staff migration preflight: no import endpoints or file upload."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.legacy_migration_gateway_v15 import (
    MigrationPreflightRefused,
    inspect_cabinet_schema_read_only,
    require_cabinet_owner,
    run_fixed_synthetic_rehearsal,
)

router = APIRouter(tags=["Legacy Migration — construction"])


def _owner_only(
    principal: models.User = Depends(require_permission("settings")),
) -> models.User:
    # require_permission -> get_current_user JWT + workstation authority gate.
    # Owner and role are verified again: team permissions/admin override alone
    # must never authorize a migration operation for another cabinet.
    try:
        require_cabinet_owner(principal)
    except MigrationPreflightRefused:
        raise HTTPException(status_code=403, detail="CABINET_OWNER_REQUIRED")
    return principal


@router.get("/preflight")
def read_only_migration_preflight(
    _owner: models.User = Depends(_owner_only),
    db: Session = Depends(database.get_db),
):
    # Only structural metadata and alembic_version are SELECTed; no patients,
    # appointments, client uploads, credentials, drafts or real clinic rows.
    return inspect_cabinet_schema_read_only(db.connection(), models.Base.metadata)


@router.post("/synthetic-rehearsal")
async def synthetic_only_migration_rehearsal(
    request: Request,
    _owner: models.User = Depends(_owner_only),
    db: Session = Depends(database.get_db),
):
    # Neither uploads nor source data or cabinet IDs can enter this endpoint.
    # Small empty JSON is allowed for an Axios POST; everything else refused.
    length = request.headers.get("content-length")
    if length is not None:
        try:
            if int(length) > 2:
                raise HTTPException(status_code=400, detail="BODY_NOT_ALLOWED")
        except ValueError:
            raise HTTPException(status_code=400, detail="BODY_NOT_ALLOWED")
    body = bytearray()
    # ASGI streaming may omit Content-Length; cap while consuming to avoid
    # a memory denial of service from a chunked file masquerading as JSON.
    async for chunk in request.stream():
        if len(body) + len(chunk) > 2:
            raise HTTPException(status_code=400, detail="BODY_NOT_ALLOWED")
        body.extend(chunk)
    if bytes(body) not in (b"", b"{}"):
        raise HTTPException(status_code=400, detail="BODY_NOT_ALLOWED")
    preflight = inspect_cabinet_schema_read_only(
        db.connection(), models.Base.metadata
    )
    if not preflight["physical_subset_checked"]:
        raise HTTPException(status_code=409, detail="PHYSICAL_SCHEMA_NOT_READY")
    try:
        report = run_fixed_synthetic_rehearsal(models.Base.metadata)
    except MigrationPreflightRefused:
        raise HTTPException(status_code=409, detail="SYNTHETIC_REHEARSAL_FAILED")
    # Runs completely in separate sqlite :memory: and rolls back. NO db.commit.
    return report.to_dict()
