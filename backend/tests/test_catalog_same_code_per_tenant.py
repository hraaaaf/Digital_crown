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


def test_same_act_code_allowed_across_tenants(db):
    a = _owner(db, "same-code-a@cabinet.test")
    b = _owner(db, "same-code-b@cabinet.test")
    sa = store.create_specialty(db, a.id, {"name": "Soins", "color": None})
    sb = store.create_specialty(db, b.id, {"name": "Soins", "color": None})

    aa = store.create_act(db, a.id, sa["id"], {
        "name": "Consultation A", "code": "C001", "base_price": 200.0,
        "color": None, "is_active": True,
    })
    bb = store.create_act(db, b.id, sb["id"], {
        "name": "Consultation B", "code": "C001", "base_price": 500.0,
        "color": None, "is_active": True,
    })

    assert aa["code"] == bb["code"] == "C001"
    assert aa["base_price"] != bb["base_price"]
