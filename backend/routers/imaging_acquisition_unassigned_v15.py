"""LOT06 B06-1 product route: authenticated read-only unassigned inventory.

This is NOT a clinical capture/preview/upload/confirm endpoint. The trusted
Windows provider is intentionally absent on startup; never take pipe names,
patient identities or device keys from an HTTP caller.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import require_permission
from backend.routers.workstation_mode import _find_workstation
from backend.services.imaging_acquisition_native_bridge_v15 import LocalNativeCaptureBridge
from tools.imaging_gateway.native_inventory_protocol_v15 import NativeInventoryDenied

router = APIRouter(tags=["Imaging acquisition — unassigned inventory"])


@router.get("/unassigned")
def get_unassigned_capture_inventory(
    request: Request,
    response: Response,
    db: Session = Depends(database.get_db),
    staff: models.User = Depends(require_permission("patients")),
):
    """Staff-only inventory, explicitly UNASSIGNED; never leaks raw media."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    if (request.client is None or request.client.host not in ("127.0.0.1", "::1")
            or not staff.is_active or staff.is_archived or staff.is_suspended
            or staff.approval_status != "approved"):
        raise HTTPException(403, "NATIVE_CAPTURE_LOCAL_STAFF_ONLY")
    tenant = int(staff.get_employer_id())
    workstation = _find_workstation(request, db, employer_id=tenant)
    if workstation is None or workstation.default_experience == "station":
        raise HTTPException(423, "NATIVE_CAPTURE_WORKSTATION_REQUIRED")

    bridge = getattr(request.app.state, "dc06_unassigned_bridge", None)
    if not isinstance(bridge, LocalNativeCaptureBridge):
        return {
            "schema_version": "dc06-product-unassigned-v1",
            "state": "NATIVE_IPC_NOT_CONNECTED",
            "read_only": True, "clinical_receipt_authorized": False,
            "patient_assigned": False, "captures": [],
        }
    try:
        capture = bridge.inventory(
            tenant_id=tenant, workstation_id=workstation.id,
        )
    except NativeInventoryDenied:
        # Never misrepresent an unreadable/refused service as an empty queue.
        raise HTTPException(503, "NATIVE_CAPTURE_INVENTORY_UNAVAILABLE") from None
    return {
        "schema_version": "dc06-product-unassigned-v1",
        "state": "UNASSIGNED_INVENTORY_READ_ONLY",
        "read_only": True, "clinical_receipt_authorized": False,
        "patient_assigned": False,
        "captures": [] if capture is None else [{
            "id": capture.id, "digest": capture.digest, "size": capture.size,
            "mime": capture.mime, "category": capture.category,
        }],
    }
