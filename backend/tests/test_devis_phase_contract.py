from backend.schemas.documents import DevisData


def test_devis_schema_drops_visual_phase_rows_before_validation():
    data = DevisData.model_validate({
        "items": [
            {"acte": "--- PHASE 1 : ASSAINISSEMENT ---", "dent": "", "prix_unitaire": 0},
            {"acte": "Composite 2 faces", "dent": "16", "dents": [16], "prix_unitaire": 700},
        ]
    })

    assert len(data.items) == 1
    assert data.items[0].acte == "Composite 2 faces"
    assert data.items[0].dents == [16]
    assert data.items[0].prix_unitaire == 700
