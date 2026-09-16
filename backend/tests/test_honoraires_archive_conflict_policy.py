from backend.services.honoraires_archive_conflict_policy import _normalize_honoraires_duplicate_payload


def test_honoraires_duplicate_normalization_ignores_linkage_metadata_only():
    incoming = {
        "payments": [{
            "date": "2026-09-14",
            "acte": "Detartrage",
            "dent": "11",
            "montant": 500.0,
        }],
        "doc_date": "2026-09-14",
    }
    archived = {
        "payments": [{
            "date": "2026-09-14",
            "acte": "Detartrage",
            "dent": "11",
            "montant": 500.0,
            "source_line_uid": "11111111-1111-1111-1111-111111111111",
            "catalog_act_id": None,
        }],
        "doc_date": "2026-09-14",
    }

    assert _normalize_honoraires_duplicate_payload(incoming) == _normalize_honoraires_duplicate_payload(archived)


def test_honoraires_duplicate_normalization_preserves_real_catalog_identity():
    left = {
        "payments": [{
            "date": "2026-09-14",
            "acte": "Acte test",
            "dent": "11",
            "montant": 500.0,
            "catalog_act_id": 10,
        }]
    }
    right = {
        "payments": [{
            "date": "2026-09-14",
            "acte": "Acte test",
            "dent": "11",
            "montant": 500.0,
            "catalog_act_id": 11,
        }]
    }

    assert _normalize_honoraires_duplicate_payload(left) != _normalize_honoraires_duplicate_payload(right)
