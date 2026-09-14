from backend.services import medication_dict


def _fixture_records():
    return [
        {
            "nom": "EXEMPLE 500 MG",
            "dci": "MOLECULE A",
            "dosage": "500",
            "unite": "MG",
            "forme": "COMPRIME",
        },
        {
            "nom": "EXEMPLE 1 G",
            "dci": "MOLECULE A",
            "dosage": "1",
            "unite": "G",
            "forme": "POUDRE",
        },
    ]


def _install_fixture(monkeypatch):
    monkeypatch.setattr(medication_dict, "_MEDS", _fixture_records())
    monkeypatch.setattr(medication_dict, "_LOADED", True)


def test_search_returns_explicit_presentation_with_provenance(monkeypatch):
    _install_fixture(monkeypatch)

    results = medication_dict.search("exemple")

    assert len(results) == 2
    first = results[0]
    assert first["presentation_id"].startswith("cnops:")
    assert first["nom"] == "EXEMPLE 500 MG"
    assert first["dosage"] == "500"
    assert first["unite"] == "MG"
    assert first["forme"] == "COMPRIME"
    assert first["source"]["id"] == "cnops-open-data-medications"
    assert first["source"]["snapshot_date"] == "2021-12-13"
    assert first["source"]["freshness"] == "historical_snapshot"
    assert first["source"]["current_marketing_status_verified"] is False


def test_presentation_id_is_stable_and_resolvable(monkeypatch):
    _install_fixture(monkeypatch)

    first_search = medication_dict.search("exemple")
    second_search = medication_dict.search("MOLECULE A")
    presentation_id = first_search[0]["presentation_id"]

    assert second_search[0]["presentation_id"] == presentation_id
    resolved = medication_dict.get_presentation(presentation_id)
    assert resolved is not None
    assert resolved["presentation_id"] == presentation_id
    assert resolved["dosage"] == "500"
    assert resolved["forme"] == "COMPRIME"


def test_unknown_presentation_fails_closed(monkeypatch):
    _install_fixture(monkeypatch)

    assert medication_dict.get_presentation("cnops:does-not-exist") is None


def test_validate_dosage_is_documentary_not_current_market_claim(monkeypatch):
    _install_fixture(monkeypatch)

    result = medication_dict.validate_dosage("EXEMPLE", 500.0)

    assert result["known"] is True
    assert result["exists"] is True
    assert 500.0 in result["available_mg"]
    assert result["source"]["current_marketing_status_verified"] is False


def test_catalog_metadata_never_claims_current_marketing_status(monkeypatch):
    _install_fixture(monkeypatch)

    metadata = medication_dict.catalog_metadata()

    assert metadata["available"] is True
    assert metadata["record_count"] == 2
    assert metadata["license"] == "ODbL"
    assert metadata["current_marketing_status_verified"] is False
