"""Compatibility facade for prescriptions + tenant-scoped clinical act search.

The certified prescription implementation remains byte-for-byte in
``prescriptions_core.py``. Only the act catalog search route is replaced here so
clinical care consumes the R6 cabinet catalog rather than the legacy global table.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.routers.auth import require_permission
from backend.services import cabinet_catalog_store as catalog_store
from backend.services.catalog_connected_truth import flatten_catalog_acts
from . import prescriptions_core as _core
from .prescriptions_core import *  # noqa: F401,F403 - compatibility facade

prescription_router = _core.prescription_router
actes_router = _core.actes_router

# Remove only the legacy global CatalogAct search handler. All care persistence,
# attachments, audit and prescription routes stay delegated to the certified core.
actes_router.routes = [
    route
    for route in actes_router.routes
    if not (
        getattr(route, "path", None) == "/catalog/search"
        and "GET" in (getattr(route, "methods", set()) or set())
    )
]


@actes_router.get("/catalog/search")
def search_catalog_acts(
    query: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical")),
):
    tenant_id = current_user.get_employer_id()
    catalog = catalog_store.list_catalog(db, tenant_id)
    return flatten_catalog_acts(catalog, query=query, limit=20)
