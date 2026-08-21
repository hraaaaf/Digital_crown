"""Compatibility facade for prescriptions + tenant-scoped clinical act catalog.

The certified prescription implementation remains byte-for-byte in
``prescriptions_core.py``. Only catalog search/quick-add are replaced so care
flows consume and write the R6 cabinet catalog instead of the legacy global one.
"""

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.routers.auth import get_current_user, require_permission
from backend.services import cabinet_catalog_store as catalog_store
from backend.services.catalog_connected_truth import flatten_catalog_acts
from . import prescriptions_core as _core
from .prescriptions_core import *  # noqa: F401,F403 - compatibility facade

prescription_router = _core.prescription_router
actes_router = _core.actes_router

# Replace only the legacy global catalog endpoints. All care persistence,
# attachments, audit and prescription routes stay delegated to the certified core.
actes_router.routes = [
    route
    for route in actes_router.routes
    if not (
        (getattr(route, "path", None) == "/catalog/search" and "GET" in (getattr(route, "methods", set()) or set()))
        or (getattr(route, "path", None) == "/catalog/quick-add" and "POST" in (getattr(route, "methods", set()) or set()))
    )
]


@actes_router.get("/catalog/search")
def search_catalog_acts(
    q: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preserve the existing q/response contract, backed only by this cabinet."""
    tenant_id = current_user.get_employer_id()
    catalog = catalog_store.list_catalog(db, tenant_id)
    return flatten_catalog_acts(catalog, query=q, limit=20)


@actes_router.post("/catalog/quick-add")
def quick_add_catalog_act(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("agenda")),
):
    """Quick-add into the same tenant catalog read by Settings and clinical care."""
    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Nom d'acte requis")
    try:
        base_price = max(0.0, float(payload.get("base_price") or 0.0))
    except (TypeError, ValueError):
        base_price = 0.0

    tenant_id = current_user.get_employer_id()
    catalog = catalog_store.list_catalog(db, tenant_id)
    for specialty in catalog:
        for act in specialty.get("acts") or []:
            if str(act.get("name") or "").strip().casefold() == name.casefold():
                if act.get("is_active") is False or float(act.get("base_price") or 0.0) != base_price:
                    updated = catalog_store.update_owned(
                        db, catalog_store.acts, int(act["id"]), tenant_id,
                        {"is_active": True, "base_price": base_price},
                    )
                    if updated:
                        act = updated
                return {
                    "id": int(act["id"]),
                    "catalog_act_id": int(act["id"]),
                    "name": act["name"],
                    "code": act.get("code"),
                    "base_price": float(act.get("base_price") or 0.0),
                    "category": specialty.get("name") or "DIVERS",
                    "is_habit": False,
                }

    category = str(payload.get("category") or "").strip() or "DIVERS"
    specialty = next(
        (row for row in catalog if str(row.get("name") or "").strip().casefold() == category.casefold()),
        None,
    )
    if specialty is None:
        specialty = catalog_store.create_specialty(db, tenant_id, {"name": category, "color": "#64748B"})

    act = catalog_store.create_act(
        db,
        tenant_id,
        int(specialty["id"]),
        {"name": name, "code": None, "base_price": base_price, "color": None, "is_active": True},
    )
    if not act:
        raise HTTPException(status_code=404, detail="Spécialité catalogue introuvable")
    return {
        "id": int(act["id"]),
        "catalog_act_id": int(act["id"]),
        "name": act["name"],
        "code": act.get("code"),
        "base_price": float(act.get("base_price") or 0.0),
        "category": specialty.get("name") or "DIVERS",
        "is_habit": False,
    }
