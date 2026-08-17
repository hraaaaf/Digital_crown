from backend import models
from backend.services import cabinet_catalog_store as store


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


def test_two_cabinets_can_use_same_specialty_and_act_code(db):
    a = _user(db, "a@cabinet.test")
    b = _user(db, "b@cabinet.test")

    sa = store.create_specialty(db, a.id, {"name": "Orthodontie", "color": "#111111"})
    sb = store.create_specialty(db, b.id, {"name": "Orthodontie", "color": "#222222"})

    aa = store.create_act(db, a.id, sa["id"], {
        "name": "Consultation", "code": "CONS", "base_price": 300.0,
        "color": None, "is_active": True,
    })
    ab = store.create_act(db, b.id, sb["id"], {
        "name": "Consultation", "code": "CONS", "base_price": 450.0,
        "color": None, "is_active": True,
    })

    assert aa["base_price"] == 300.0
    assert ab["base_price"] == 450.0
    assert store.list_catalog(db, a.id)[0]["acts"][0]["base_price"] == 300.0
    assert store.list_catalog(db, b.id)[0]["acts"][0]["base_price"] == 450.0


def test_cross_tenant_update_is_refused(db):
    a = _user(db, "owner-a@cabinet.test")
    b = _user(db, "owner-b@cabinet.test")
    sa = store.create_specialty(db, a.id, {"name": "Implantologie", "color": None})

    changed = store.update_owned(db, store.specialties, sa["id"], b.id, {"name": "Volé"})

    assert changed is None
    assert store.list_catalog(db, a.id)[0]["name"] == "Implantologie"
    assert store.list_catalog(db, b.id) == []


def test_ambiguous_legacy_catalog_is_not_claimed(db):
    _user(db, "root-one@cabinet.test")
    _user(db, "root-two@cabinet.test")
    legacy = models.Specialty(name="Legacy global", color="#123456")
    db.add(legacy)
    db.commit()

    store.claim_legacy_if_unambiguous(db)

    rows = db.execute(store.specialties.select()).mappings().all()
    assert rows == []
    assert db.query(models.Specialty).filter(models.Specialty.name == "Legacy global").count() == 1
