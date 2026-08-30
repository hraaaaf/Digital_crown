"""Marketplace P3 — split transactionnel d'un panier multi-fournisseurs."""

from backend import database, models
from backend.main import app


def _override_partner_db(db):
    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db


def _make_supplier(db, user, name: str, *, active: bool = True):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=name.lower().replace(" ", "-"),
        name=name,
        is_active=active,
        sync_mode="manual",
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def _make_product(
    db,
    user,
    supplier,
    *,
    name: str,
    sku: str,
    price: float,
    availability=models.PartnerProductAvailability.AVAILABLE,
):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name=name,
        sku=sku,
        dental_category="Consommables",
        dental_specialty="Omnipratique",
        unit="boite",
        price=price,
        availability=availability,
        benefits_json=[],
        is_featured=False,
        sort_order=0,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def _payload(*products, quantities=None):
    quantities = quantities or [1] * len(products)
    return {
        "partnerId": "client-supplier-ignored",
        "partnerName": "Client supplier ignored",
        "strategyLabel": "Client label ignored",
        "settlementBasis": "SENT_TO_PARTNER",
        "revenueModel": "COMMISSION_PERCENT",
        "commissionRate": 10.0,
        "discountRate": 0.0,
        "fixedFeeAmount": 0.0,
        "customer": {
            "fullName": "Acheteur P3",
            "clinic": "Cabinet P3",
            "phone": "0600000000",
            "email": "buyer-p3@test.ma",
            "city": "Rabat",
            "note": "split",
        },
        "lines": [
            {
                "productId": str(product.id),
                "name": "client-line-ignored",
                "sku": "CLIENT-SKU",
                "quantity": quantity,
                "unitPrice": 0.01,
                "lineTotal": 0.01,
            }
            for product, quantity in zip(products, quantities)
        ],
        "estimatedTotal": 0.01,
    }


def test_http_cart_with_two_suppliers_creates_two_canonical_orders_atomically(client, db, dentiste, auth_headers):
    _override_partner_db(db)
    supplier_a = _make_supplier(db, dentiste, "P3 Supplier A")
    supplier_b = _make_supplier(db, dentiste, "P3 Supplier B")
    product_a = _make_product(db, dentiste, supplier_a, name="Produit A", sku="P3-A", price=100.0)
    product_b = _make_product(db, dentiste, supplier_b, name="Produit B", sku="P3-B", price=50.0)

    response = client.post(
        "/api/partner-orders",
        json=_payload(product_a, product_b, quantities=[2, 3]),
        headers=auth_headers,
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["batchId"].startswith("LOT-PART-")
    assert body["orderNumber"] == body["batchId"]
    assert body["orderCount"] == 2
    assert body["strategyLabel"] == "Commission sur commande envoyée"
    assert body["estimatedTotal"] == 350.0

    orders = body["orders"]
    assert [order["partnerId"] for order in orders] == [str(supplier_a.id), str(supplier_b.id)]
    assert [order["partnerName"] for order in orders] == ["P3 Supplier A", "P3 Supplier B"]
    assert orders[0]["estimatedTotal"] == 200.0
    assert orders[1]["estimatedTotal"] == 150.0
    assert orders[0]["lines"][0]["sku"] == "P3-A"
    assert orders[0]["lines"][0]["unitPrice"] == 100.0
    assert orders[1]["lines"][0]["sku"] == "P3-B"
    assert orders[1]["lines"][0]["unitPrice"] == 50.0

    persisted_orders = db.query(models.PartnerOrder).order_by(models.PartnerOrder.id.asc()).all()
    assert len(persisted_orders) == 2
    events = db.query(models.PartnerOrderEvent).order_by(models.PartnerOrderEvent.id.asc()).all()
    assert len(events) == 2
    assert {event.payload_json["batchId"] for event in events} == {body["batchId"]}
    assert {event.payload_json["pricingAuthority"] for event in events} == {"SERVER_CATALOG"}


def test_invalid_line_in_mixed_cart_rolls_back_entire_batch(client, db, dentiste, auth_headers):
    _override_partner_db(db)
    supplier_a = _make_supplier(db, dentiste, "P3 Atomic A")
    supplier_b = _make_supplier(db, dentiste, "P3 Atomic B")
    valid = _make_product(db, dentiste, supplier_a, name="Valide", sku="P3-OK", price=80.0)
    discontinued = _make_product(
        db,
        dentiste,
        supplier_b,
        name="Retire",
        sku="P3-KO",
        price=40.0,
        availability=models.PartnerProductAvailability.DISCONTINUED,
    )

    response = client.post(
        "/api/partner-orders",
        json=_payload(valid, discontinued),
        headers=auth_headers,
    )

    assert response.status_code == 422, response.text
    assert "retire du catalogue" in response.json()["detail"]
    assert db.query(models.PartnerOrder).count() == 0
    assert db.query(models.PartnerOrderEvent).count() == 0


def test_interleaved_lines_keep_deterministic_supplier_and_line_order(client, db, dentiste, auth_headers):
    _override_partner_db(db)
    supplier_a = _make_supplier(db, dentiste, "P3 Deterministic A")
    supplier_b = _make_supplier(db, dentiste, "P3 Deterministic B")
    product_a1 = _make_product(db, dentiste, supplier_a, name="A1", sku="P3-A1", price=10.0)
    product_b = _make_product(db, dentiste, supplier_b, name="B", sku="P3-B1", price=20.0)
    product_a2 = _make_product(db, dentiste, supplier_a, name="A2", sku="P3-A2", price=30.0)

    response = client.post(
        "/api/partner-orders",
        json=_payload(product_a1, product_b, product_a2),
        headers=auth_headers,
    )

    assert response.status_code == 201, response.text
    orders = response.json()["orders"]
    assert [order["partnerId"] for order in orders] == [str(supplier_a.id), str(supplier_b.id)]
    assert [line["sku"] for line in orders[0]["lines"]] == ["P3-A1", "P3-A2"]
    assert [line["sku"] for line in orders[1]["lines"]] == ["P3-B1"]
