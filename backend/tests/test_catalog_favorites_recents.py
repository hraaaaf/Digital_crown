from datetime import datetime

from backend import models
from backend.services import cabinet_catalog_store as store


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


def _employee(db, owner, email: str):
    user = models.User(
        email=email,
        hashed_password="x",
        role=models.UserRole.DENTISTE,
        is_active=True,
        is_licensed=True,
        nom_complet=email,
        employer_id=owner.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_catalog_favorite_and_recent_are_personal_practitioner_preferences(db):
    owner = _owner(db, "favorite-recent@cabinet.test")
    colleague = _employee(db, owner, "colleague@cabinet.test")
    specialty = store.create_specialty(db, owner.id, {"name": "CONSERVATRICE", "color": "#123456"})
    act = store.create_act(db, owner.id, specialty["id"], {
        "name": "Composite test",
        "code": "CUSTOM-FAV-1",
        "base_price": 0.0,
        "color": None,
        "is_active": True,
    })

    assert store.set_catalog_act_favorite(db, owner.id, owner.id, act["id"], True)
    assert store.record_catalog_act_usage(
        db,
        owner.id,
        owner.id,
        act_name="Composite test",
        specialty_name="CONSERVATRICE",
    ) is True

    owner_act = next(
        item for spec in store.list_catalog(db, owner.id, owner.id)
        for item in spec["acts"] if item["id"] == act["id"]
    )
    colleague_act = next(
        item for spec in store.list_catalog(db, owner.id, colleague.id)
        for item in spec["acts"] if item["id"] == act["id"]
    )

    assert owner_act["is_favorite"] is True
    assert owner_act["usage_count"] == 1
    assert isinstance(owner_act["last_used_at"], datetime)
    assert colleague_act["is_favorite"] is False
    assert colleague_act["usage_count"] == 0
    assert colleague_act["last_used_at"] is None


def test_recent_usage_refuses_ambiguous_same_name_without_specialty(db):
    owner = _owner(db, "recent-ambiguous@cabinet.test")
    first = store.create_specialty(db, owner.id, {"name": "A", "color": "#111111"})
    second = store.create_specialty(db, owner.id, {"name": "B", "color": "#222222"})
    for specialty in (first, second):
        store.create_act(db, owner.id, specialty["id"], {
            "name": "Acte partagé",
            "code": f"CUSTOM-{specialty['id']}",
            "base_price": 0.0,
            "color": None,
            "is_active": True,
        })

    assert store.record_catalog_act_usage(
        db,
        owner.id,
        owner.id,
        act_name="Acte partagé",
    ) is False
