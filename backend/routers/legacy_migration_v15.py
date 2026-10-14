"""Authenticated staff migration preflight: no import endpoints or file upload."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.services.legacy_migration_gateway_v15 import (
    MigrationPreflightRefused,
    inspect_cabinet_schema_read_only,
    require_cabinet_owner,
    run_fixed_synthetic_rehearsal,
)

from backend.services.legacy_migration_synthetic_file_v15 import (
    MAX_FIXTURE_BYTES, SyntheticFileRefused, build_synthetic_fixture_bytes,
    rehearse_uploaded_synthetic_sqlite,
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


@router.get("/synthetic-fixture")
def download_official_synthetic_sqlite(
    _owner: models.User = Depends(_owner_only),
):
    """All 300 rows are fake; never reads/exports clinic patients."""
    content = build_synthetic_fixture_bytes()
    return Response(
        content=content, media_type="application/vnd.sqlite3",
        headers={
            "Content-Disposition": 'attachment; filename="digital-crown-synthetic-100x200.db"',
            "Cache-Control": "no-store, private",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/synthetic-file-dryrun")
async def dryrun_official_synthetic_sqlite_file(
    request: Request,
    _owner: models.User = Depends(_owner_only),
    db: Session = Depends(database.get_db),
):
    """Upload exact official demo .db binary; zero source/target persistence.

    DO NOT generalize into a real legacy file handler. It intentionally rejects
    arbitrary vendor/clinic databases even with a synthetic marker table.
    """
    if request.headers.get("content-type", "").split(";")[0].lower().strip() != "application/vnd.sqlite3":
        raise HTTPException(status_code=415, detail="SYNTHETIC_SQLITE_CONTENT_TYPE_REQUIRED")
    size = request.headers.get("content-length")
    if size is not None:
        try:
            nbytes = int(size)
        except ValueError:
            raise HTTPException(status_code=400, detail="INVALID_UPLOAD_LENGTH")
        if not 0 < nbytes <= MAX_FIXTURE_BYTES:
            raise HTTPException(status_code=413, detail="SYNTHETIC_FILE_TOO_LARGE")
    # Streaming bounded, including when Content-Length is missing or forged.
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_FIXTURE_BYTES:
            raise HTTPException(status_code=413, detail="SYNTHETIC_FILE_TOO_LARGE")
        content.extend(chunk)
    if not content:
        raise HTTPException(status_code=400, detail="EMPTY_SYNTHETIC_FILE")
    preflight = inspect_cabinet_schema_read_only(
        db.connection(), models.Base.metadata
    )
    if not preflight["physical_subset_checked"]:
        raise HTTPException(status_code=409, detail="PHYSICAL_SCHEMA_NOT_READY")
    try:
        return rehearse_uploaded_synthetic_sqlite(bytes(content), models.Base.metadata)
    except (SyntheticFileRefused, MigrationPreflightRefused):
        # No patient/value/file content or backend path ever echoed.
        raise HTTPException(status_code=422, detail="SYNTHETIC_FIXTURE_REJECTED")
