from backend.services import medication_dict


def _current(row):
    return {**row, "_source": dict(medication_dict.AMMPS_CURRENT_SOURCE)}


def _install(monkeypatch, rows):
    monkeypatch.setattr(medication_dict, "_MEDS", [_current(row) for row in rows])
    monkeypatch.setattr(medication_dict, "_LOADED", True)


def test_dol_brand_prefix_beats_internal_substring(monkeypatch):
    _install(monkeypatch, [
        {"nom": "ANDOL", "dci": "PARACETAMOL", "dosage": "500", "unite": "MG", "forme": "COMPRIME", "presentation": "B20", "epi": "X"},
        {"nom": "CLARADOL PLUS", "dci": "PARACETAMOL", "dosage": "500", "unite": "MG", "forme": "COMPRIME", "presentation": "B20", "epi": "X"},
        {"nom": "DOLIPRANE", "dci": "PARACETAMOL", "dosage": "500", "unite": "MG", "forme": "COMPRIME", "presentation": "B16", "epi": "X"},
        {"nom": "SEVREDOL", "dci": "MORPHINE", "dosage": "20", "unite": "MG", "forme": "COMPRIME", "presentation": "B14", "epi": "X"},
    ])

    results = medication_dict.search_unified("DOL", limit=10)

    assert [r["nom"] for r in results][:4] == [
        "DOLIPRANE",
        "ANDOL",
        "CLARADOL PLUS",
        "SEVREDOL",
    ]


def test_exact_brand_beats_brand_prefix(monkeypatch):
    _install(monkeypatch, [
        {"nom": "DOLIPRANE EXTRA", "dci": "PARACETAMOL", "dosage": "500", "unite": "MG", "forme": "COMPRIME", "presentation": "B16", "epi": "X"},
        {"nom": "DOLIPRANE", "dci": "PARACETAMOL", "dosage": "500", "unite": "MG", "forme": "COMPRIME", "presentation": "B16", "epi": "X"},
    ])

    results = medication_dict.search_unified("DOLIPRANE", limit=10)

    assert [r["nom"] for r in results][:2] == ["DOLIPRANE", "DOLIPRANE EXTRA"]


def test_dci_prefix_is_deterministic(monkeypatch):
    _install(monkeypatch, [
        {"nom": "BRAND B", "dci": "AMOXICILLINE", "dosage": "500", "unite": "MG", "forme": "GELULE", "presentation": "B12", "epi": "X"},
        {"nom": "BRAND A", "dci": "AMOXICILLINE", "dosage": "1", "unite": "G", "forme": "COMPRIME", "presentation": "B14", "epi": "X"},
    ])

    a = medication_dict.search_unified("AMOX", limit=10)
    b = medication_dict.search_unified("AMOX", limit=10)

    assert [r["regulatory_presentation_id"] for r in a] == [r["regulatory_presentation_id"] for r in b]
    assert [r["nom"] for r in a] == ["BRAND A", "BRAND B"]
