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


def test_cannot_create_act_under_foreign_specialty(db):
    a = _owner(db, "foreign-parent-a@cabinet.test")
    b = _owner(db, "foreign-parent-b@cabinet.test")
    specialty = store.create_specialty(db, a.id, {"name": "Chirurgie", "color": None})

    result = store.create_act(db, b.id, specialty["id"], {
        "name": "Intrusion", "code": "X-FOREIGN", "base_price": 1.0,
        "color": None, "is_active": True,
    })

    assert result is None
    assert store.list_catalog(db, b.id) == []
