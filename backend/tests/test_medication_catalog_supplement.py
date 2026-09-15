from backend.services import medication_dict


def _reload_catalog() -> None:
    medication_dict._LOADED = False
    medication_dict._MEDS = []
    medication_dict._SUPPLEMENT_COUNT = 0
    medication_dict._SUPPLEMENT_SOURCES = []


def test_acig_partial_search_returns_two_sourced_presentations():
    _reload_catalog()
    results = medication_dict.search("ACIG")
    assert [item["nom"] for item in results] == ["ACIGAM 100 MG", "ACIGAM 200 MG"]
    assert [item["dosage"] for item in results] == ["100", "200"]
    assert all(item["unite"] == "MG" for item in results)
    assert all(item["forme"] == "COMPRIME SECABLE" for item in results)
    assert all(item["dci"] == "ACIDE TIAPROFÉNIQUE" for item in results)
    assert all(item["presentation_id"].startswith("ma-doc:") for item in results)
    assert all(item["source"]["id"] == "ma-acigam-official-plus-crosscheck-2026-01-16" for item in results)
    assert all(item["source"]["current_marketing_status_verified"] is False for item in results)


def test_acig_presentation_resolution_preserves_source_provenance():
    _reload_catalog()
    result = medication_dict.search("ACIG", limit=1)[0]
    resolved = medication_dict.get_presentation(result["presentation_id"])
    assert resolved is not None
    assert resolved["nom"] == "ACIGAM 100 MG"
    assert resolved["source"]["source_url"].startswith("https://www.sante.gov.ma/")
    assert len(resolved["source"]["evidence"]) == 2


def test_acig_dosage_validation_uses_supplement_source():
    _reload_catalog()
    result = medication_dict.validate_dosage("ACIGAM", 100)
    assert result["known"] is True
    assert result["exists"] is True
    assert result["available_mg"] == [100.0, 200.0]
    assert result["dci"] == "ACIDE TIAPROFÉNIQUE"
    assert result["source"]["id"] == "ma-acigam-official-plus-crosscheck-2026-01-16"


def test_base_cnops_results_remain_available_and_keep_original_source():
    _reload_catalog()
    results = medication_dict.search("AMOXICILLINE", limit=5)
    assert results
    assert all(item["presentation_id"].startswith("cnops:") for item in results)
    assert any(item["source"]["id"] == "cnops-open-data-medications" for item in results)


def test_metadata_exposes_supplement_without_claiming_current_availability():
    _reload_catalog()
    metadata = medication_dict.catalog_metadata()
    assert metadata["supplement_record_count"] == 2
    assert metadata["record_count"] >= 4234
    source = next(item for item in metadata["sources"] if item["id"] == "ma-acigam-official-plus-crosscheck-2026-01-16")
    assert source["current_marketing_status_verified"] is False
