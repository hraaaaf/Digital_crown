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


def test_d7_document_route_resolves_active_media_root(tmp_path, monkeypatch):
    import backend.routers.documents as documents

    active_root = tmp_path / "neo-d7-rehearsal-media"
    stale_root = tmp_path / "previous-media"
    monkeypatch.setattr(documents, "MEDIA_DIR", stale_root)
    monkeypatch.setattr(documents, "get_media_root", lambda: active_root)

    relative_key = "static/archives/1/ordonnance/2026/10/ordonnance.pdf"
    resolved = documents._archive_storage_path(relative_key)
    assert resolved == active_root / "archives/1/ordonnance/2026/10/ordonnance.pdf"
    assert not resolved.is_relative_to(stale_root)
    resolved.parent.mkdir(parents=True)
    resolved.write_bytes(b"%PDF-synthetic-test")
    assert documents._archive_storage_path(relative_key).is_file()
