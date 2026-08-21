from decimal import Decimal
from pathlib import Path

from backend.services.catalog_connected_truth import flatten_catalog_acts


def test_flatten_catalog_acts_preserves_public_contract_and_filters_inactive():
    catalog = [
        {
            "name": "Prévention",
            "acts": [
                {"id": 1, "name": "Détartrage", "code": "DET-001", "base_price": Decimal("500.00"), "is_active": True},
                {"id": 2, "name": "Acte masqué", "code": "OLD", "base_price": 100, "is_active": False},
            ],
        }
    ]
    assert flatten_catalog_acts(catalog, "DET-001") == [
        {
            "id": "cat_1",
            "catalog_act_id": 1,
            "name": "Détartrage",
            "code": "DET-001",
            "base_price": 500.0,
            "price": 500.0,
            "category": "Prévention",
            "is_habit": False,
        }
    ]
    assert flatten_catalog_acts(catalog, "OLD") == []


def test_clinical_search_and_quick_add_use_same_tenant_r6_catalog():
    source = Path("backend/routers/prescriptions.py").read_text(encoding="utf-8")
    assert 'q: str = ""' in source
    assert "current_user.get_employer_id()" in source
    assert "catalog_store.list_catalog(db, tenant_id)" in source
    assert "flatten_catalog_acts(catalog, query=q" in source
    assert 'route, "path", None) == "/catalog/quick-add"' in source
    assert "catalog_store.create_act" in source
    assert "models.CatalogAct" not in source


def test_master_plan_validates_new_snapshot_tenant_but_reuses_history():
    source = Path("backend/routers/patient_master_plan_p3.py").read_text(encoding="utf-8")
    model = Path("backend/models_catalog_plan.py").read_text(encoding="utf-8")
    assert "TreatmentPlanCatalogSnapshot" in source
    assert "catalog_store.get_owned(db, catalog_store.acts, act_id, tenant_id)" in source
    assert "Acte catalogue indisponible pour ce cabinet" in source
    assert "_same_snapshot(explicit, preserved)" in source
    assert "snapshot = queue.popleft()" in source
    assert "revision_snapshot" in source
    assert "treatment_plan_catalog_snapshots" in model
    assert "Numeric(12, 2)" in model
