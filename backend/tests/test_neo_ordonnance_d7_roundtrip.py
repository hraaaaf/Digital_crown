from backend.schemas.documents import MedicationItem


def test_medication_item_preserves_d7_safety_and_catalog_identity():
    item = MedicationItem.model_validate({
        "nom": "DOLIPRANE",
        "dosage": "1 G",
        "forme": "COMPRIME EFFERVESCENT SECABLE",
        "posologie": "1 comprimé matin et soir pendant 3 jours",
        "quantite": 3,
        "quantite_explicit": True,
        "non_substituable": True,
        "catalog_presentation_id": "ammps:test",
        "catalog_dci": "PARACETAMOL",
        "catalog_source_id": "ammps-current",
        "catalog_source_label": "AMMPS",
        "catalog_snapshot_date": "2026-10-01",
        "catalog_marketing_status_verified": True,
    })
    data = item.model_dump()
    assert data["non_substituable"] is True
    assert data["catalog_presentation_id"] == "ammps:test"
    assert data["catalog_dci"] == "PARACETAMOL"
    assert data["catalog_source_id"] == "ammps-current"
    assert data["catalog_marketing_status_verified"] is True
