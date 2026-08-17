from sqlalchemy import select, func

from backend import models
from backend.services import cabinet_catalog_store as store


def test_single_root_cabinet_claims_legacy_catalog_once(db):
    owner = models.User(
        email="single-root@cabinet.test",
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet="Single Root",
    )
    db.add(owner)
    db.flush()

    legacy_specialty = models.Specialty(name="Parodontologie", color="#445566")
    db.add(legacy_specialty)
    db.flush()
    db.add(models.CatalogAct(
        specialty_id=legacy_specialty.id,
        name="Détartrage",
        code="DET",
        base_price=350.0,
        color=None,
        is_active=True,
    ))
    db.commit()

    first = store.list_catalog(db, owner.id)
    second = store.list_catalog(db, owner.id)
    count = db.execute(select(func.count()).select_from(store.specialties)).scalar_one()

    assert len(first) == 1
    assert first[0]["name"] == "Parodontologie"
    assert first[0]["acts"][0]["code"] == "DET"
    assert first[0]["acts"][0]["base_price"] == 350.0
    assert second == first
    assert count == 1
