from backend import database, models
from backend.config import settings
from backend.main import app
from backend.models_marketplace_stock import MarketplaceStockMovement


def _override_db(db):
    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db


def _grant_platform_authority(monkeypatch, user):
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", user.id)


def _fixture_rows(db, user, *, suffix: str):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=f"p7-bridge-{suffix}",
        name=f"P7 Bridge {suffix}",
        sync_mode="manual",
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name=f"Produit Bridge {suffix}",
        sku=f"P7-BRIDGE-{suffix}",
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=100.0,
        availability=models.PartnerProductAvailability.AVAILABLE,
        benefits_json=[],
    )
    stock_item = models.StockItem(
        employer_id=user.get_employer_id(),
        nom=f"Stock Bridge {suffix}",
        categorie=models.StockCategorie.CONSOMMABLE,
        quantite=1.0,
        seuil_alerte=2.0,
        unite="unite",
    )
    db.add_all([product, stock_item])
    db.commit()
    db.refresh(product)
    db.refresh(stock_item)

    order = models.PartnerOrder(
        employer_id=user.get_employer_id(),
        order_number=f"P7-BRIDGE-ORDER-{suffix}",
        partner_id=str(supplier.id),
        partner_name=supplier.name,
        status=models.PartnerOrderStatus.CONFIRMED,
        customer_full_name="Dr Bridge",
        customer_clinic="Cabinet Bridge",
        customer_phone="0600000000",
        customer_email="bridge@example.test",
        customer_city="Rabat",
        lines_json=[{
            "productId": str(product.id),
            "name": product.name,
            "sku": product.sku,
            "quantity": 2,
            "unitPrice": 100.0,
        }],
        estimated_total=200.0,
        sent_total=200.0,
        current_total=200.0,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return product, stock_item, order


def _mapping(client, headers, product, stock_item):
    response = client.put(
        f"/api/stock/marketplace/mappings/{product.id}",
        headers=headers,
        json={
            "stockItemId": stock_item.id,
            "stockUnitsPerProductUnit": 2,
            "minQuantity": 2,
            "targetQuantity": 10,
            "isActive": True,
        },
    )
    assert response.status_code == 200, response.text


def _receipt_payload(key: str, product_id: int):
    return {
        "idempotencyKey": key,
        "lines": [{
            "productId": str(product_id),
            "quantityReceived": 2,
            "lotNumber": "LOT-BRIDGE",
            "expiresAt": "2027-03-01T00:00:00",
        }],
        "note": "Réception P7 bridge",
    }


def test_receipt_http_automatically_updates_mapped_stock(client, db, dentiste, auth_headers, monkeypatch):
    _override_db(db)
    _grant_platform_authority(monkeypatch, dentiste)
    product, stock_item, order = _fixture_rows(db, dentiste, suffix="AUTO")
    _mapping(client, auth_headers, product, stock_item)

    response = client.post(
        f"/api/partner-orders/{order.id}/receipt",
        headers=auth_headers,
        json=_receipt_payload("bridge-auto-0001", product.id),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["stockSync"] == {
        "status": "APPLIED",
        "idempotentReplay": False,
        "movementCount": 1,
    }
    db.refresh(stock_item)
    assert stock_item.quantite == 5.0

    replay = client.post(
        f"/api/partner-orders/{order.id}/receipt",
        headers=auth_headers,
        json=_receipt_payload("bridge-auto-0001", product.id),
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["idempotentReplay"] is True
    assert replay.json()["stockSync"]["status"] == "APPLIED"
    assert replay.json()["stockSync"]["idempotentReplay"] is True
    db.refresh(stock_item)
    assert stock_item.quantite == 5.0
    assert db.query(MarketplaceStockMovement).filter(MarketplaceStockMovement.receipt_id == body["receipt"]["id"]).count() == 1


def test_receipt_survives_missing_mapping_then_replay_repairs_stock(client, db, dentiste, auth_headers, monkeypatch):
    _override_db(db)
    _grant_platform_authority(monkeypatch, dentiste)
    product, stock_item, order = _fixture_rows(db, dentiste, suffix="PENDING")
    payload = _receipt_payload("bridge-pending-0001", product.id)

    first = client.post(f"/api/partner-orders/{order.id}/receipt", headers=auth_headers, json=payload)
    assert first.status_code == 201, first.text
    assert first.json()["idempotentReplay"] is False
    assert first.json()["stockSync"] == {
        "status": "PENDING_MAPPING",
        "productIds": [product.id],
    }
    db.refresh(stock_item)
    assert stock_item.quantite == 1.0

    _mapping(client, auth_headers, product, stock_item)
    replay = client.post(f"/api/partner-orders/{order.id}/receipt", headers=auth_headers, json=payload)
    assert replay.status_code == 201, replay.text
    assert replay.json()["idempotentReplay"] is True
    assert replay.json()["stockSync"]["status"] == "APPLIED"
    assert replay.json()["stockSync"]["idempotentReplay"] is False
    db.refresh(stock_item)
    assert stock_item.quantite == 5.0

    second_replay = client.post(f"/api/partner-orders/{order.id}/receipt", headers=auth_headers, json=payload)
    assert second_replay.status_code == 201, second_replay.text
    assert second_replay.json()["stockSync"]["idempotentReplay"] is True
    db.refresh(stock_item)
    assert stock_item.quantite == 5.0
