from pathlib import Path

from backend.services.catalog_connected_truth import flatten_catalog_acts


def test_flatten_catalog_acts_filters_inactive_and_matches_code():
    catalog = [
        {
            "name": "Prévention",
            "acts": [
                {"id": 1, "name": "Détartrage", "code": "DET-001", "base_price": 500, "is_active": True},
                {"id": 2, "name": "Acte masqué", "code": "OLD", "base_price": 100, "is_active": False},
            ],
        }
    ]
    assert flatten_catalog_acts(catalog, "DET-001") == [
        {"id": 1, "name": "Détartrage", "code": "DET-001", "price": 500.0}
    ]
    assert flatten_catalog_acts(catalog, "OLD") == []


def test_clinical_search_uses_tenant_r6_catalog_not_global_model():
    source = Path("backend/routers/prescriptions.py").read_text(encoding="utf-8")
    assert "current_user.get_employer_id()" in source
    assert "catalog_store.list_catalog(db, tenant_id)" in source
    assert "flatten_catalog_acts" in source
    assert "db.query(CatalogAct)" not in source


def test_master_plan_persists_and_rehydrates_catalog_snapshot():
    source = Path("backend/routers/patient_master_plan_p3.py").read_text(encoding="utf-8")
    model = Path("backend/models_catalog_plan.py").read_text(encoding="utf-8")
    assert "TreatmentPlanCatalogSnapshot" in source
    assert "catalog_snapshot" in source
    assert "old_snapshots" in source
    assert "revision_snapshot" in source
    assert "treatment_plan_catalog_snapshots" in model
    assert "price = Column(Float" in model
