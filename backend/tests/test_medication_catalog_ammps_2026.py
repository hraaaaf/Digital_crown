from backend.services import medication_dict


def test_acig_search_uses_ammps_2026_source():
    results = medication_dict.search("ACIG", limit=15)

    assert results
    acigam = next(item for item in results if item["nom"].startswith("ACIGAM 200 MG"))
    assert acigam["dci"] == "ACIDE TIAPROFENIQUE"
    assert acigam["dosage"] == "200"
    assert acigam["unite"] == "MG"
    assert acigam["forme"] == "COMPRIME SECABLE"
    assert acigam["source"]["id"] == "ammps-rmmg-2026-01"
    assert acigam["source"]["snapshot_date"] == "2026-01"
    assert acigam["source"]["current_marketing_status_verified"] is False
    assert acigam["ean13"] == "6118000041986"
    assert acigam["epi"] == "BOTTU"


def test_acig_presentation_resolves_by_stable_ammps_id():
    result = medication_dict.search("ACIG", limit=1)[0]
    assert result["presentation_id"].startswith("ammps:")

    resolved = medication_dict.get_presentation(result["presentation_id"])
    assert resolved is not None
    assert resolved["nom"] == result["nom"]
    assert resolved["source"]["id"] == "ammps-rmmg-2026-01"


def test_existing_cnops_result_keeps_existing_source_and_id_prefix():
    results = medication_dict.search("DISPAMOX", limit=5)
    assert results
    assert results[0]["presentation_id"].startswith("cnops:")
    assert results[0]["source"]["id"] == "cnops-open-data-medications"


def test_catalog_metadata_exposes_both_sources_without_overstating_marketing_status():
    metadata = medication_dict.catalog_metadata()

    source_ids = {source["id"] for source in metadata["sources"]}
    assert "cnops-open-data-medications" in source_ids
    assert "ammps-rmmg-2026-01" in source_ids
    assert metadata["record_count"] >= 4235
    ammps = next(source for source in metadata["sources"] if source["id"] == "ammps-rmmg-2026-01")
    assert ammps["record_count"] >= 1
    assert ammps["current_marketing_status_verified"] is False


def test_validate_acig_is_documentary_only_and_uses_ammps_provenance():
    result = medication_dict.validate_dosage("ACIGAM", 200)

    assert result["known"] is True
    assert result["exists"] is True
    assert result["dci"] == "ACIDE TIAPROFENIQUE"
    assert result["source"]["id"] == "ammps-rmmg-2026-01"
