from datetime import datetime

from backend import database, models
from backend.config import settings
from backend.main import app
from backend.models_marketplace_receipts import PartnerOrderReceipt
from backend.models_marketplace_stock import MarketplaceStockLot, MarketplaceStockMovement


def _override_db(db):
    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db


def _supplier(db, user, key="p7-supplier"):
    row = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=key,
        name=f"Supplier {key}",
        sync_mode="manual",
        is_active=True,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _product(db, user, supplier, sku="P7-001", name="Produit P7"):
    row = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name=name,
        sku=sku,
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=100.0,
        availability=models.PartnerProductAvailability.AVAILABLE,
        benefits_json=[],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _stock_item(db, user, name="Stock P7", quantity=0.0):
    row = models.StockItem(
        employer_id=user.get_employer_id(),
        nom=name,
        categorie=models.StockCategorie.CONSOMMABLE,
        quantite=quantity,
        seuil_alerte=2.0,
        unite="unite",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _order(db, user, supplier, lines, number="P7-ORDER-001"):
    row = models.PartnerOrder(
        employer_id=user.get_employer_id(),
        order_number=number,
        partner_id=str(supplier.id),
        partner_name=supplier.name,
        status=models.PartnerOrderStatus.CONFIRMED,
        customer_full_name="Dr P7",
        customer_clinic="Cabinet P7",
        customer_phone="0600000000",
        customer_email="p7@example.test",
        customer_city="Rabat",
        lines_json=lines,
        estimated_total=100.0,
        sent_total=100.0,
        current_total=100.0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _receipt(db, user, order, key, lines):
    row = PartnerOrderReceipt(
        employer_id=user.get_employer_id(),
        order_id=order.id,
        receipt_key=key,
        received_by_user_id=user.id,
        lines_json=lines,
        received_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _map(client, headers, product, stock_item, *, factor=1.0, minimum=2.0, target=8.0):
    response = client.put(
        f"/api/stock/marketplace/mappings/{product.id}",
        headers=headers,
        json={
            "stockItemId": stock_item.id,
            "stockUnitsPerProductUnit": factor,
            "minQuantity": minimum,
            "targetQuantity": target,
            "isActive": True,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_receipt_apply_is_atomic_idempotent_and_tracks_lot(client, db, dentiste, auth_headers, monkeypatch):
    _override_db(db)
    monkeypatch.setattr(settings, "SUPERADMIN_EMAIL", dentiste.email)
    supplier = _supplier(db, dentiste)
    product = _product(db, dentiste, supplier)
    stock_item = _stock_item(db, dentiste, quantity=2.0)
    _map(client, auth_headers, product, stock_item, factor=2.0, minimum=3.0, target=12.0)
    order = _order(
        db,
        dentiste,
        supplier,
        [{"productId": str(product.id), "name": product.name, "sku": product.sku, "quantity": 3, "unitPrice": 100.0}],
    )
    receipt = _receipt(
        db,
        dentiste,
        order,
        "receipt-p7-0001",
        [{
            "productId": str(product.id),
            "name": product.name,
            "sku": product.sku,
            "quantityOrdered": 3,
            "quantityReceived": 3,
            "lotNumber": "LOT-P7-A",
            "expiresAt": "2027-02-01T00:00:00",
        }],
    )

    first = client.post(f"/api/stock/marketplace/receipts/{receipt.id}/apply", headers=auth_headers)
    assert first.status_code == 201, first.text
    assert first.json()["idempotentReplay"] is False
    db.refresh(stock_item)
    assert stock_item.quantite == 8.0

    lots = client.get(f"/api/stock/marketplace/lots?stock_item_id={stock_item.id}", headers=auth_headers)
    assert lots.status_code == 200, lots.text
    assert lots.json()[0]["lotNumber"] == "LOT-P7-A"
    assert lots.json()[0]["quantity"] == 6.0
    assert lots.json()[0]["expiresAt"] == "2027-02-01T00:00:00"

    replay = client.post(f"/api/stock/marketplace/receipts/{receipt.id}/apply", headers=auth_headers)
    assert replay.status_code == 201, replay.text
    assert replay.json()["idempotentReplay"] is True
    db.refresh(stock_item)
    assert stock_item.quantite == 8.0
    assert db.query(MarketplaceStockMovement).filter(MarketplaceStockMovement.receipt_id == receipt.id).count() == 1


def test_missing_mapping_rejects_whole_receipt_without_stock_mutation(client, db, dentiste, auth_headers, monkeypatch):
    _override_db(db)
    monkeypatch.setattr(settings, "SUPERADMIN_EMAIL", dentiste.email)
    supplier = _supplier(db, dentiste, key="p7-atomic")
    product_a = _product(db, dentiste, supplier, sku="P7-A", name="Produit A")
    product_b = _product(db, dentiste, supplier, sku="P7-B", name="Produit B")
    stock_item = _stock_item(db, dentiste, quantity=4.0)
    _map(client, auth_headers, product_a, stock_item, factor=1.0, minimum=2.0, target=10.0)
    order = _order(
        db,
        dentiste,
        supplier,
        [
            {"productId": str(product_a.id), "name": product_a.name, "sku": product_a.sku, "quantity": 1, "unitPrice": 50.0},
            {"productId": str(product_b.id), "name": product_b.name, "sku": product_b.sku, "quantity": 1, "unitPrice": 50.0},
        ],
        number="P7-ORDER-ATOMIC",
    )
    receipt = _receipt(
        db,
        dentiste,
        order,
        "receipt-p7-atomic",
        [
            {"productId": str(product_a.id), "quantityReceived": 1, "lotNumber": "A1"},
            {"productId": str(product_b.id), "quantityReceived": 1, "lotNumber": "B1"},
        ],
    )

    response = client.post(f"/api/stock/marketplace/receipts/{receipt.id}/apply", headers=auth_headers)
    assert response.status_code == 409, response.text
    assert response.json()["detail"]["code"] == "STOCK_MAPPING_MISSING"
    db.refresh(stock_item)
    assert stock_item.quantite == 4.0
    assert db.query(MarketplaceStockMovement).count() == 0
    assert db.query(MarketplaceStockLot).count() == 0


def test_consumption_uses_fefo_is_idempotent_and_drives_reorder(client, db, dentiste, auth_headers, monkeypatch):
    _override_db(db)
    monkeypatch.setattr(settings, "SUPERADMIN_EMAIL", dentiste.email)
    supplier = _supplier(db, dentiste, key="p7-fefo")
    product = _product(db, dentiste, supplier, sku="P7-FEFO", name="Produit FEFO")
    stock_item = _stock_item(db, dentiste, quantity=0.0)
    _map(client, auth_headers, product, stock_item, factor=2.0, minimum=4.0, target=10.0)
    order = _order(
        db,
        dentiste,
        supplier,
        [{"productId": str(product.id), "name": product.name, "sku": product.sku, "quantity": 4, "unitPrice": 25.0}],
        number="P7-ORDER-FEFO",
    )
    receipt_a = _receipt(
        db,
        dentiste,
        order,
        "receipt-p7-fefo-a",
        [{"productId": str(product.id), "quantityReceived": 2, "lotNumber": "EARLY", "expiresAt": "2026-10-01T00:00:00"}],
    )
    receipt_b = _receipt(
        db,
        dentiste,
        order,
        "receipt-p7-fefo-b",
        [{"productId": str(product.id), "quantityReceived": 2, "lotNumber": "LATE", "expiresAt": "2027-01-01T00:00:00"}],
    )
    assert client.post(f"/api/stock/marketplace/receipts/{receipt_a.id}/apply", headers=auth_headers).status_code == 201
    assert client.post(f"/api/stock/marketplace/receipts/{receipt_b.id}/apply", headers=auth_headers).status_code == 201
    db.refresh(stock_item)
    assert stock_item.quantite == 8.0

    consume = client.post(
        f"/api/stock/marketplace/items/{stock_item.id}/consume",
        headers=auth_headers,
        json={"quantity": 5, "idempotencyKey": "consume-p7-0001", "note": "Usage clinique"},
    )
    assert consume.status_code == 201, consume.text
    assert consume.json()["stockQuantity"] == 3.0
    assert consume.json()["movement"]["allocations"] == [
        {"lotId": consume.json()["movement"]["allocations"][0]["lotId"], "lotNumber": "EARLY", "quantity": 4.0},
        {"lotId": consume.json()["movement"]["allocations"][1]["lotId"], "lotNumber": "LATE", "quantity": 1.0},
    ]

    replay = client.post(
        f"/api/stock/marketplace/items/{stock_item.id}/consume",
        headers=auth_headers,
        json={"quantity": 5, "idempotencyKey": "consume-p7-0001", "note": "Usage clinique"},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["idempotentReplay"] is True
    db.refresh(stock_item)
    assert stock_item.quantite == 3.0

    lots = client.get(f"/api/stock/marketplace/lots?stock_item_id={stock_item.id}", headers=auth_headers).json()
    by_lot = {item["lotNumber"]: item["quantity"] for item in lots}
    assert by_lot == {"EARLY": 0.0, "LATE": 3.0}

    suggestions = client.get("/api/stock/marketplace/reorder-suggestions", headers=auth_headers)
    assert suggestions.status_code == 200, suggestions.text
    assert suggestions.json() == [{
        "productId": product.id,
        "productName": product.name,
        "sku": product.sku,
        "supplierId": supplier.id,
        "availability": "AVAILABLE",
        "stockItemId": stock_item.id,
        "stockItemName": stock_item.nom,
        "currentQuantity": 3.0,
        "minQuantity": 4.0,
        "targetQuantity": 10.0,
        "suggestedOrderUnits": 4,
        "projectedQuantity": 11.0,
    }]


def test_mapping_is_tenant_scoped(client, db, dentiste, auth_headers):
    _override_db(db)
    outsider = models.User(
        email="outsider-p7@example.test",
        hashed_password="not-used",
        role="DENTISTE",
        nom_complet="Outsider P7",
        is_active=True,
        is_licensed=True,
    )
    db.add(outsider)
    db.commit()
    db.refresh(outsider)
    supplier = _supplier(db, outsider, key="p7-outsider")
    outsider_product = _product(db, outsider, supplier, sku="P7-OUT", name="Produit outsider")
    own_stock = _stock_item(db, dentiste, name="Stock owner", quantity=1.0)

    response = client.put(
        f"/api/stock/marketplace/mappings/{outsider_product.id}",
        headers=auth_headers,
        json={
            "stockItemId": own_stock.id,
            "stockUnitsPerProductUnit": 1,
            "minQuantity": 1,
            "targetQuantity": 5,
            "isActive": True,
        },
    )
    assert response.status_code == 404
