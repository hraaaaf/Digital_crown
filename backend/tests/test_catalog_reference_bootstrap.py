from backend import models
from backend.services import cabinet_catalog_store as store
from backend.services.catalog_reference_library import REFERENCE_CATALOG_VERSION


def _owner(db, email: str):
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


def test_reference_catalog_apply_is_explicit_idempotent_and_price_free(db):
    owner = _owner(db, "reference@cabinet.test")
    assert store.list_catalog(db, owner.id) == []

    first = store.apply_reference_catalog(db, owner.id)
    second = store.apply_reference_catalog(db, owner.id)
    catalog = store.list_catalog(db, owner.id)

    assert first["applied"] is True
    assert first["acts_added"] >= 150
    assert second == {"applied": False, "specialties_added": 0, "acts_added": 0}
    assert sum(len(specialty["acts"]) for specialty in catalog) >= 150
    assert all(
        act["base_price"] == 0
        for specialty in catalog
        for act in specialty["acts"]
    )

    state = db.execute(
        store.catalog_reference_state.select().where(
            store.catalog_reference_state.c.employer_id == owner.id
        )
    ).mappings().one()
    assert state["version"] == REFERENCE_CATALOG_VERSION


def test_reference_catalog_never_overwrites_existing_price_or_custom_act(db):
    owner = _owner(db, "preserve@cabinet.test")
    specialty = store.create_specialty(
        db, owner.id, {"name": "CONSERVATRICE", "color": "#123456"}
    )
    custom = store.create_act(db, owner.id, specialty["id"], {
        "name": "Acte maison",
        "code": "CUSTOM-HOUSE",
        "base_price": 777.0,
        "color": None,
        "is_active": True,
    })

    store.apply_reference_catalog(db, owner.id)
    catalog = store.list_catalog(db, owner.id)
    all_acts = [act for specialty in catalog for act in specialty["acts"]]
    preserved = next(act for act in all_acts if act["id"] == custom["id"])

    assert preserved["name"] == "Acte maison"
    assert preserved["base_price"] == 777.0
    assert preserved["code"] == "CUSTOM-HOUSE"
