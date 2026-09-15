import json
from pathlib import Path

from backend.services import medication_dict


def test_regulatory_identity_distinguishes_ammps_packaging_without_breaking_legacy_id():
    rows = medication_dict.search_regulatory_presentations("AMOXICILLINE LLORENTE")
    current = [row for row in rows if row["source"]["id"] == "ammps-medications-current-2026-09-15"]

    assert {row["presentation"] for row in current} == {"BOITE DE 12", "BOITE DE 24"}
    assert len({row["presentation_id"] for row in current}) == 1
    assert len({row["regulatory_presentation_id"] for row in current}) == 2
    assert all(row["regulatory_presentation_id"].startswith("ammps-reg:") for row in current)
    assert {row["amm_status"] for row in current} == {"PENDING_VERIFICATION"}


def test_historical_search_keeps_deduplicated_contract():
    rows = [
        row
        for row in medication_dict.search("AMOXICILLINE LLORENTE", limit=20)
        if row["source"]["id"] == "ammps-medications-current-2026-09-15"
    ]
    assert len(rows) == 1


def test_current_snapshot_separates_market_and_amm_status_by_package():
    rows = medication_dict.search_regulatory_presentations("CLAMOXYL")
    current = [row for row in rows if row["source"]["id"] == "ammps-medications-current-2026-09-15"]
    by_package = {row["presentation"]: row for row in current}

    assert by_package["FLACON DE 60 ML"]["amm_status"] == "AMM ENREGISTREE"
    assert by_package["FLACON DE 60 ML"]["market_status"] == "Commercialisé"
    assert by_package["FLACON DE 100 ML"]["amm_status"] == "AMM RETIREE"
    assert by_package["FLACON DE 100 ML"]["market_status"] == "Retiré du Marché"
    assert by_package["FLACON DE 60 ML"]["presentation_id"] == by_package["FLACON DE 100 ML"]["presentation_id"]
    assert by_package["FLACON DE 60 ML"]["regulatory_presentation_id"] != by_package["FLACON DE 100 ML"]["regulatory_presentation_id"]


def test_get_regulatory_presentation_resolves_exact_package():
    row = next(
        item
        for item in medication_dict.search_regulatory_presentations("AMOXICILLINE SP")
        if item.get("presentation") == "BOITE DE 24" and item.get("dosage") == "1"
    )
    resolved = medication_dict.get_regulatory_presentation(row["regulatory_presentation_id"])

    assert resolved is not None
    assert resolved["presentation"] == "BOITE DE 24"
    assert resolved["market_status"] == "Commercialisé AO"
    assert resolved["amm_status"] == "PENDING_VERIFICATION"
    assert resolved["source"]["current_marketing_status_verified"] is True


def test_catalog_metadata_preserves_cnops_contract_and_exposes_current_ammps_source():
    metadata = medication_dict.catalog_metadata()

    assert metadata["id"] == "cnops-open-data-medications"
    assert metadata["record_count"] == 4234
    assert metadata["available"] is True

    current = next(
        source for source in metadata["sources"]
        if source["id"] == "ammps-medications-current-2026-09-15"
    )
    assert current["record_count"] == 8
    assert current["current_marketing_status_verified"] is True
    assert current["snapshot_date"] == "2026-09-15"


def test_m1_seed_is_documentary_only_and_rcp_validation_is_fail_closed():
    root = Path(__file__).resolve().parents[2]
    rows = json.loads(
        (root / "backend/data/medications_ma_ammps_current_2026.json").read_text(encoding="utf-8")
    )

    forbidden_clinical_fields = {"regimen", "posology", "duration", "dose_per_day", "automation_tier"}
    for row in rows:
        assert forbidden_clinical_fields.isdisjoint(row)
        assert row["market_status_checked_at"] == "2026-09-15"
        assert row["rcp_snapshot_status"] == "PENDING_DOWNLOAD"
        assert row["rcp_sha256"] is None
        assert row["rcp_checked_at"] is None
