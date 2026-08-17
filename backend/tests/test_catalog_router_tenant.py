from types import SimpleNamespace

from fastapi import HTTPException

from backend.routers import catalog
from backend.schemas.catalog import SpecialtyCreate, SpecialtyUpdate


def _user(user_id: int, employer_id=None):
    return SimpleNamespace(id=user_id, employer_id=employer_id, get_employer_id=lambda: employer_id or user_id)


def test_router_cross_tenant_specialty_update_returns_404(db):
    owner_a = _user(101)
    owner_b = _user(202)

    created = catalog.create_specialty(
        SpecialtyCreate(name="Endodontie", color="#111111"), db=db, current_user=owner_a
    )

    try:
        catalog.update_specialty(
            created["id"], SpecialtyUpdate(name="Intrusion"), db=db, current_user=owner_b
        )
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        raise AssertionError("cross-tenant update must fail closed")
