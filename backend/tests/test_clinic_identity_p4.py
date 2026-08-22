"""P4B runtime truth tests for practitioner vs organization identity."""
from sqlalchemy import inspect

from backend import database, models
from backend.models_identity_p4 import migrate_identity_columns
from backend.security import get_password_hash


def _make_owner(db, email="p4b-owner@test.ma"):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Legacy User",
        is_active=True,
        is_licensed=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_cabinet(db, owner):
    config = models.CabinetConfig(
        owner_id=owner.id,
        nom_cabinet="Cabinet Canonique",
        nom_praticien="Dr Legacy Cabinet",
        nom_praticien_ar="طبيب قديم",
        inpe="LEGACY-AMBIGUOUS",
        is_initialized=True,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    client.cookies.clear()
    return headers


def test_identity_columns_are_registered_and_migration_is_idempotent():
    migrate_identity_columns(database.engine)
    migrate_identity_columns(database.engine)

    inspector = inspect(database.engine)
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    cabinet_columns = {column["name"] for column in inspector.get_columns("cabinet_configs")}

    assert {"nom_complet_ar", "inpe_professionnel"} <= user_columns
    assert "inpe_etablissement" in cabinet_columns


def test_practitioner_round_trip_updates_user_only(client, db):
    owner = _make_owner(db)
    cabinet = _make_cabinet(db, owner)
    headers = _headers(client, owner)

    response = client.patch(
        "/api/clinics/me/practitioner",
        json={
            "nom_complet": "Dr Canonique",
            "nom_complet_ar": "د. قانوني",
            "inpe_professionnel": "INPE-PRO-001",
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["nom_complet"] == "Dr Canonique"
    assert response.json()["nom_complet_ar"] == "د. قانوني"
    assert response.json()["inpe_professionnel"] == "INPE-PRO-001"

    db.refresh(owner)
    db.refresh(cabinet)
    assert owner.nom_complet == "Dr Canonique"
    assert owner.nom_complet_ar == "د. قانوني"
    assert owner.inpe_professionnel == "INPE-PRO-001"
    # No silent back-write into the legacy CabinetConfig practitioner identity.
    assert cabinet.nom_praticien == "Dr Legacy Cabinet"
    assert cabinet.nom_praticien_ar == "طبيب قديم"
    assert cabinet.inpe == "LEGACY-AMBIGUOUS"

    get_response = client.get("/api/clinics/me/practitioner", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["nom_complet"] == "Dr Canonique"


def test_establishment_inpe_updates_cabinet_without_reclassifying_legacy(client, db):
    owner = _make_owner(db, "p4b-establishment@test.ma")
    cabinet = _make_cabinet(db, owner)
    headers = _headers(client, owner)

    response = client.put(
        "/api/clinics/me",
        json={"inpe_etablissement": "INPE-EST-001"},
        headers=headers,
    )
    assert response.status_code == 200, response.text

    db.refresh(cabinet)
    assert cabinet.inpe_etablissement == "INPE-EST-001"
    assert cabinet.inpe == "LEGACY-AMBIGUOUS"
    assert owner.inpe_professionnel is None


def test_practitioner_identity_rejects_subaccount_even_with_settings_permission(client, db):
    owner = _make_owner(db, "p4b-boss@test.ma")
    _make_cabinet(db, owner)
    child = models.User(
        email="p4b-child@test.ma",
        hashed_password=get_password_hash("TestPass123!"),
        role="DENTISTE",
        nom_complet="Dr Child",
        is_active=True,
        is_licensed=True,
        employer_id=owner.id,
        permissions={"settings": True},
    )
    db.add(child)
    db.commit()
    db.refresh(child)
    headers = _headers(client, child)

    response = client.patch(
        "/api/clinics/me/practitioner",
        json={"nom_complet": "Dr Should Not Win"},
        headers=headers,
    )
    assert response.status_code == 403

    db.refresh(owner)
    assert owner.nom_complet == "Dr Legacy User"


def test_practitioner_identity_rejects_unknown_fields(client, db):
    owner = _make_owner(db, "p4b-extra@test.ma")
    headers = _headers(client, owner)

    response = client.patch(
        "/api/clinics/me/practitioner",
        json={"nom_complet": "Dr Valid", "nom_cabinet": "Wrong owner"},
        headers=headers,
    )
    assert response.status_code == 422
