"""MOB-5D — preuve d'isolation cabinet et RBAC du Stock partagé desktop/mobile."""
from backend import models
from backend.security import get_password_hash


def _make_user(db, email: str, *, role: str = "DENTISTE", permissions=None, employer_id=None):
    user = models.User(
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        role=role,
        nom_complet="Stock Test",
        is_active=True,
        is_licensed=True,
        permissions={} if permissions is None else permissions,
        employer_id=employer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _headers(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.email, "password": "TestPass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_item(client, headers, name: str):
    response = client.post(
        "/api/stock/items",
        json={
            "nom": name,
            "categorie": "CONSOMMABLE",
            "quantite": 2,
            "seuil_alerte": 3,
            "unite": "boîtes",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_stock_is_tenant_scoped_and_subaccount_uses_employer_cabinet(client, db):
    owner_a = _make_user(db, "stock-owner-a@test.ma")
    owner_b = _make_user(db, "stock-owner-b@test.ma")
    assistant_a = _make_user(
        db,
        "stock-assistant-a@test.ma",
        role="SECRETAIRE",
        permissions={"patients": True},
        employer_id=owner_a.id,
    )

    item_a = _create_item(client, _headers(client, owner_a), "Article cabinet A")
    item_b = _create_item(client, _headers(client, owner_b), "Article cabinet B")

    owner_a_list = client.get("/api/stock/items", headers=_headers(client, owner_a))
    assert owner_a_list.status_code == 200, owner_a_list.text
    assert [item["id"] for item in owner_a_list.json()] == [item_a["id"]]

    assistant_list = client.get("/api/stock/items", headers=_headers(client, assistant_a))
    assert assistant_list.status_code == 200, assistant_list.text
    assert [item["id"] for item in assistant_list.json()] == [item_a["id"]]

    cross_tenant_patch = client.patch(
        f"/api/stock/items/{item_b['id']}",
        json={"quantite": 99},
        headers=_headers(client, assistant_a),
    )
    assert cross_tenant_patch.status_code == 404

    owner_b_list = client.get("/api/stock/items", headers=_headers(client, owner_b))
    assert owner_b_list.status_code == 200, owner_b_list.text
    assert owner_b_list.json()[0]["id"] == item_b["id"]
    assert owner_b_list.json()[0]["quantite"] == 2


def test_stock_respects_explicit_patients_permission_denial(client, db):
    owner = _make_user(db, "stock-owner-deny@test.ma")
    denied = _make_user(
        db,
        "stock-denied@test.ma",
        role="SECRETAIRE",
        permissions={"patients": False},
        employer_id=owner.id,
    )

    response = client.get("/api/stock/items", headers=_headers(client, denied))
    assert response.status_code == 403
