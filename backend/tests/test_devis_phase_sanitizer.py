from backend.utils.devis_phase_sanitizer import (
    is_devis_phase_presentation_row,
    strip_devis_phase_presentation_rows,
)


def test_detects_only_legacy_phase_presentation_rows():
    assert is_devis_phase_presentation_row({"acte": "--- PHASE 1 : ASSAINISSEMENT ---", "prix_unitaire": 0})
    assert not is_devis_phase_presentation_row({"acte": "Couronne", "prix_unitaire": 3500})
    assert not is_devis_phase_presentation_row({"acte": "--- remise", "prix_unitaire": -200})


def test_strips_phase_rows_without_mutating_real_quote_rows():
    real_row = {"acte": "Composite 2 faces", "dent": "16", "prix_unitaire": 700}
    rows = [
        {"acte": "--- PHASE 1 : ASSAINISSEMENT ---", "prix_unitaire": 0},
        real_row,
        {"acte": "--- PHASE 3 : PROTHÉTIQUE ---", "prix_unitaire": 0},
    ]

    assert strip_devis_phase_presentation_rows(rows) == [real_row]
    assert rows[1] is real_row
