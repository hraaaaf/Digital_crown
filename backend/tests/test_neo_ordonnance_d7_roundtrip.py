from backend.schemas.documents import MedicationItem


def test_d7_preserves_explicit_quantity_ns_and_catalog_identity():
    source = {
        "nom": "DOLIPRANE",
        "dosage": "1 G",
        "forme": "COMPRIME EFFERVESCENT SECABLE",
        "posologie": "1 comprimé matin et soir pendant 3 jours",
        "quantite": 3,
        "quantite_explicit": True,
        "non_substituable": True,
        "catalog_presentation_id": "ammps:synthetic-test",
        "catalog_dci": "PARACETAMOL",
        "catalog_source_id": "ammps-synthetic",
        "catalog_source_label": "AMMPS TEST",
        "catalog_snapshot_date": "2026-09-15",
        "catalog_marketing_status_verified": False,
    }
    data = MedicationItem.model_validate(source).model_dump()
    for key, expected in source.items():
        assert data[key] == expected
