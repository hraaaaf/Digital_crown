"""Owner-only Station printer policy status + emergency DISABLE.

No API to enable printing, register printers, attest physical safety,
download PDFs, route Station documents or release paper.
"""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import get_current_user
from backend.routers.workstation_mode import _require_pin
from backend.services.station_document_print_inventory import (
    enrolled_stations_for_tenant,
    independently_certified_printers_for_tenant,
)
from backend.services.station_document_print_store import (
    PrintConfigurationConflict,
    load_effective_configuration,
    save_owner_configuration,
)
from backend.services.station_document_print_configuration import PrintConfigurationRejected
from backend.services.station_print_admin_boundary import (
    StationPrintAdminDenied, require_cabinet_root_owner,
    require_same_origin_mutation,
)
from backend.utils.rate_limit import (
    enforce_failure_rate_limit, record_rate_limit_failure,
)

router = APIRouter(tags=["Station Print Configuration"])
get_db = database.get_db


class DisableStationPrinting(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expectedRevision: int = Field(ge=0)
    ownerPin: str = Field(pattern=r"^\d{4,8}$")
    mode: Literal["disabled"]
    stationIds: list[str] = Field(default_factory=list, max_length=0)
    printerIds: list[str] = Field(default_factory=list, max_length=0)


class CabinetClinicalPreflightRequest(BaseModel):
    """Selectors only. No actor identity, clinical flags, printer attestation,
    file path or PDF bytes accepted from browser payloads."""
    model_config = ConfigDict(extra="forbid")
    sessionId: str = Field(min_length=36, max_length=36)
    documentId: int = Field(gt=0)
    archiveSha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    ownerPin: str = Field(pattern=r"^\\d{4,8}$")



def _owner(user: models.User) -> int:
    tenant_id = int(user.get_employer_id())
    try:
        require_cabinet_root_owner(
            actor_user_id=user.id,
            actor_employer_id=user.employer_id,
            tenant_id=tenant_id,
        )
    except StationPrintAdminDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return tenant_id


def _safe_inventory(db: Session, tenant_id: int):
    # Source is DB, not user-provided printer flags. No physical registry,
    # therefore no printer can be enabled through this API.
    connection = db.connection()
    stations = enrolled_stations_for_tenant(connection, tenant_id=tenant_id)
    printers = independently_certified_printers_for_tenant(connection, tenant_id=tenant_id)
    return stations, printers


@router.post("/station-print-config/clinical-check")
def check_cabinet_print_clinical_readiness(
    body: CabinetClinicalPreflightRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Auth/PIN/CSRF-protected, read-only clinical readiness check.

    Returns no patient, PDF, spool command, print permit or document details.
    The Station cannot access this endpoint due to get_current_user's
    workstation gate AND explicit registered Cabinet cookie resolution.
    """
    from backend.routers.workstation_mode import _find_workstation
    from backend.services.station_print_cabinet_clinical_gate_v15 import (
        clinically_recheck_cabinet_print,
    )

    tenant_id = _owner(current_user)
    try:
        require_same_origin_mutation(
            expected_base=str(request.base_url),
            origin=request.headers.get("origin"),
            fetch_site=request.headers.get("sec-fetch-site"),
            has_auth_cookie=bool(request.cookies.get("access_token")),
            has_bearer_token=bool(request.headers.get("authorization", "").startswith("Bearer ")),
        )
    except StationPrintAdminDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    scope = f"station_print_clinical_check:{tenant_id}"
    enforce_failure_rate_limit(request, scope=scope, max_attempts=5)
    try:
        _require_pin(db, current_user, body.ownerPin)
    except HTTPException as exc:
        if exc.detail == "Invalid owner PIN":
            record_rate_limit_failure(request, scope)
        raise

    workstation = _find_workstation(request, db, tenant_id)
    if workstation is None or workstation.default_experience != "cabinet":
        raise HTTPException(status_code=403, detail="CABINET_WORKSTATION_REQUIRED")

    # Clinical facts are verified using the same live DB transaction.
    # With the trusted printer registry absent, even a fully valid care
    # sheet cannot create a print job. Never disclose clinical reason codes
    # that could become a document-presence oracle to an HTTP client.
    result = clinically_recheck_cabinet_print(
        db,
        authenticated_user=current_user,
        authenticated_workstation=workstation,
        session_id=body.sessionId,
        document_id=body.documentId,
        expected_sha256=body.archiveSha256,
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "printing_unavailable",
        "printingAvailable": False,
        "claimCreated": False,
        "archiveVerified": False,
    }


@router.get("/station-print-config")
def get_station_print_config(
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tenant_id = _owner(current_user)
    trusted_stations, trusted_printers = _safe_inventory(db, tenant_id)
    result = load_effective_configuration(
        db.get_bind(), tenant_id=tenant_id,
        trusted_stations=trusted_stations, trusted_printers=trusted_printers,
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "mode": result.policy.mode,
        "revision": result.revision,
        "status": result.reason,
        "printingAvailable": False,
        "configurationEnableSupported": False,
    }


@router.put("/station-print-config")
def disable_station_printing(
    body: DisableStationPrinting,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tenant_id = _owner(current_user)
    try:
        require_same_origin_mutation(
            expected_base=str(request.base_url),
            origin=request.headers.get("origin"),
            fetch_site=request.headers.get("sec-fetch-site"),
            has_auth_cookie=bool(request.cookies.get("access_token")),
            has_bearer_token=bool(request.headers.get("authorization", "").startswith("Bearer ")),
        )
    except StationPrintAdminDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    scope = f"station_print_admin_disable:{tenant_id}"
    enforce_failure_rate_limit(request, scope=scope, max_attempts=5)
    try:
        _require_pin(db, current_user, body.ownerPin)
    except HTTPException as exc:
        if exc.detail == "Invalid owner PIN":
            record_rate_limit_failure(request, scope)
        raise

    trusted_stations, trusted_printers = _safe_inventory(db, tenant_id)
    try:
        revision = save_owner_configuration(
            db.get_bind(), tenant_id=tenant_id,
            actor_user_id=int(current_user.id), actor_employer_id=current_user.employer_id,
            expected_revision=body.expectedRevision,
            proposal={
                "schemaVersion": 1, "mode": "disabled",
                "stationIds": [], "printerIds": [],
            },
            trusted_stations=trusted_stations,
            trusted_printers=trusted_printers,
        )
    except PrintConfigurationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PrintConfigurationRejected as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response.headers["Cache-Control"] = "no-store"
    return {
        "mode": "disabled", "revision": revision,
        "status": "printing_disabled",
        "printingAvailable": False,
        "configurationEnableSupported": False,
    }
