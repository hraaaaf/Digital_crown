"""Marketplace P4 — recherche, filtres et pagination catalogue."""

from backend import database, models
from backend.main import app


def _override_catalog_db(db):
    def _get_db():
        yield db

    app.dependency_overrides[database.get_db] = _get_db


def _make_supplier(db, user, *, key: str, name: str):
    supplier = models.PartnerSupplier(
        employer_id=user.get_employer_id(),
        supplier_key=key,
        name=name,
        is_active=True,
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
    category: str = "Consommables",
    specialty: str = "Omnipratique",
    sort_order: int = 0,
    short_description: str | None = None,
    long_description: str | None = None,
    featured: bool = False,
):
    product = models.PartnerCatalogProduct(
        employer_id=user.get_employer_id(),
        supplier_id=supplier.id,
        name=name,
        sku=sku,
        dental_category=category,
        dental_specialty=specialty,
        unit="boite",
        price=100.0,
        availability=models.PartnerProductAvailability.AVAILABLE,
        short_description=short_description,
        long_description=long_description,
        benefits_json=[],
        is_featured=featured,
        sort_order=sort_order,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def test_http_catalog_combines_supplier_category_specialty_and_text_search(client, db, dentiste, auth_headers):
    _override_catalog_db(db)
    supplier_a = _make_supplier(db, dentiste, key="p4-a", name="P4 Supplier A")
    supplier_b = _make_supplier(db, dentiste, key="p4-b", name="P4 Supplier B")
    target = _make_product(
        db,
        dentiste,
        supplier_a,
        name="Lime endodontique premium",
        sku="ENDO-P4",
        category="Endodontie",
        specialty="Endodontie",
        short_description="instrument nickel titane",
        long_description="séquence clinique rotative",
    )
    _make_product(
        db,
        dentiste,
        supplier_a,
        name="Composite universel",
        sku="RESTO-P4",
        category="Restauration",
        specialty="Omnipratique",
    )
    long_description_match = _make_product(
        db,
        dentiste,
        supplier_b,
        name="Couronne laboratoire",
        sku="LAB-P4",
        category="Restauration",
        specialty="Prothèse",
        long_description="bloc zircone multicouche",
    )

    filtered = client.get(
        "/api/partner-catalog/products",
        params={
            "supplier_id": supplier_a.id,
            "category": "Endodontie",
            "specialty": "Endodontie",
            "q": "nickel",
        },
        headers=auth_headers,
    )
    long_search = client.get(
        "/api/partner-catalog/products",
        params={"q": "zircone"},
        headers=auth_headers,
    )

    assert filtered.status_code == 200, filtered.text
    assert [item["id"] for item in filtered.json()] == [target.id]
    assert long_search.status_code == 200, long_search.text
    assert [item["id"] for item in long_search.json()] == [long_description_match.id]


def test_http_product_pagination_is_stable_and_preserves_merchandising_metadata(client, db, dentiste, auth_headers):
    _override_catalog_db(db)
    supplier = _make_supplier(db, dentiste, key="p4-page", name="P4 Pagination")
    products = [
        _make_product(db, dentiste, supplier, name="P1", sku="P4-1", sort_order=1, featured=True),
        _make_product(db, dentiste, supplier, name="P2", sku="P4-2", sort_order=2),
        _make_product(db, dentiste, supplier, name="P3", sku="P4-3", sort_order=3),
        _make_product(db, dentiste, supplier, name="P4", sku="P4-4", sort_order=4),
    ]

    first_page = client.get(
        "/api/partner-catalog/products",
        params={"offset": 0, "limit": 2},
        headers=auth_headers,
    )
    second_page = client.get(
        "/api/partner-catalog/products",
        params={"offset": 2, "limit": 2},
        headers=auth_headers,
    )

    assert first_page.status_code == 200, first_page.text
    assert second_page.status_code == 200, second_page.text
    assert [item["id"] for item in first_page.json()] == [products[0].id, products[1].id]
    assert [item["id"] for item in second_page.json()] == [products[2].id, products[3].id]
    assert first_page.json()[0]["isFeatured"] is True
    assert first_page.json()[0]["sortOrder"] == 1


def test_http_supplier_pagination_uses_stable_name_order(client, db, dentiste, auth_headers):
    _override_catalog_db(db)
    _make_supplier(db, dentiste, key="p4-c", name="Charlie")
    bravo = _make_supplier(db, dentiste, key="p4-b", name="Bravo")
    _make_supplier(db, dentiste, key="p4-a", name="Alpha")

    response = client.get(
        "/api/partner-catalog/suppliers",
        params={"offset": 1, "limit": 1},
        headers=auth_headers,
    )

    assert response.status_code == 200, response.text
    assert [item["id"] for item in response.json()] == [bravo.id]


def test_http_catalog_rejects_invalid_pagination_bounds(client, db, dentiste, auth_headers):
    _override_catalog_db(db)
    _make_supplier(db, dentiste, key="p4-limits", name="Limits")

    negative_offset = client.get(
        "/api/partner-catalog/products",
        params={"offset": -1},
        headers=auth_headers,
    )
    zero_limit = client.get(
        "/api/partner-catalog/suppliers",
        params={"limit": 0},
        headers=auth_headers,
    )
    oversized_limit = client.get(
        "/api/partner-catalog/products",
        params={"limit": 501},
        headers=auth_headers,
    )

    assert negative_offset.status_code == 422
    assert zero_limit.status_code == 422
    assert oversized_limit.status_code == 422
