from fastapi import HTTPException

from backend import models
from backend.routers import catalog
from backend.schemas.catalog import SpecialtyCreate, SpecialtyUpdate


def _user(db, email: str):
    user = models.User(
        email=email,
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet=email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_router_cross_tenant_specialty_update_returns_404(db):
    owner_a = _user(db, "router-a@cabinet.test")
    owner_b = _user(db, "router-b@cabinet.test")

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
