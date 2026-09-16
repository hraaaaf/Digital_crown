import copy

import pytest

from backend.services.ngap_dental_reference import (
    EXPECTED_ENTRY_COUNT,
    EXPECTED_SOURCE_SHA256,
    index_ngap_dental_reference,
    load_ngap_dental_bundle,
    load_ngap_dental_conditions,
    load_ngap_dental_reference,
    load_ngap_dental_provenance,
    validate_ngap_dental_conditions,
    validate_ngap_dental_reference,
    validate_ngap_dental_provenance,
)


def test_ngap_dental_reference_is_locked_and_reference_only():
    payload = load_ngap_dental_reference()
    assert payload["dataset_id"] == "ngap-dental-177-06-v1"
    assert payload["status"] == "REFERENCE_ONLY_NOT_RUNTIME_CERTIFIED"
    assert payload["reference"]["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert payload["reference"]["publication"] == "Bulletin officiel n° 5414 du 20 avril 2006"
    assert len(payload["acts"]) == EXPECTED_ENTRY_COUNT == 145


def test_ngap_dental_reference_has_exact_expected_coverage():
    payload = load_ngap_dental_reference()
    codes = [row[0] for row in payload["acts"]]
    assert codes == [
        *(f"D{value}" for value in range(600, 642)),
        *(f"D{value}" for value in range(700, 786)),
        *(f"D{value}" for value in range(800, 817)),
    ]
    assert len(codes) == len(set(codes))


def test_ngap_dental_reference_sentinel_mappings():
    entries = index_ngap_dental_reference()
    assert entries["D626"]["coefficient"] == 15
    assert entries["D627"]["coefficient"] == 5
    assert entries["D700"]["coefficient"] == 10
    assert entries["D704"]["coefficient"] == 10
    assert entries["D708"]["coefficient"] == 12
    assert entries["D713"]["coefficient"] == 10
    assert "permanente" in entries["D713"]["acte"].lower()
    assert entries["D720"]["coefficient"] == 40
    assert entries["D738"]["coefficient"] == 15
    assert entries["D754"]["coefficient"] == 180
    assert entries["D773"]["coefficient"] == 120
    assert entries["D800"]["coefficient"] == 25


def test_non_fixed_rules_do_not_invent_coefficients():
    entries = index_ngap_dental_reference()
    assert entries["D630"]["entry_type"] == "ceiling"
    assert entries["D630"]["coefficient"] == 540
    assert entries["D757"]["entry_type"] == "calculation_rule"
    assert entries["D757"]["coefficient"] is None
    assert entries["D816"]["entry_type"] == "quote_required"
    assert entries["D816"]["coefficient"] is None


def test_anesthesia_column_is_preserved_when_source_lists_it():
    entries = index_ngap_dental_reference()
    assert entries["D600"]["coefficient"] == 50
    assert entries["D600"]["anesthesia_coefficient"] == 20
    assert entries["D614"]["coefficient"] == 200
    assert entries["D614"]["anesthesia_coefficient"] == 90
    assert entries["D726"]["coefficient"] == 50
    assert entries["D726"]["anesthesia_coefficient"] == 30


def test_conditions_are_source_bound_and_keep_distinct_rules():
    payload = load_ngap_dental_conditions()
    rules = payload["conditions"]
    assert payload["reference"]["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert "D608" in rules
    assert "D626" in rules
    assert "D628" in rules
    assert "D712" in rules
    assert rules["D738-D741"].startswith("Radiographie obligatoire")
    assert rules["D739-D741"].startswith("Marsupialisation")


def test_mapping_conditions_and_locked_binary_share_exact_source_hash():
    bundle = load_ngap_dental_bundle()
    assert (
        bundle["reference"]["reference"]["source_sha256"]
        == bundle["conditions"]["reference"]["source_sha256"]
        == bundle["provenance"]["locked_binary"]["sha256"]
        == EXPECTED_SOURCE_SHA256
    )


def test_locked_binary_provenance_does_not_equate_discovery_urls():
    payload = load_ngap_dental_provenance()
    locked = payload["locked_binary"]
    assert locked["filename"] == "bo_5414_fr.pdf"
    assert locked["page_count"] == 220
    assert locked["byte_size"] == 11334738
    assert all(
        source["role"] == "TEXT_CORROBORATION_NOT_LOCKED_BINARY"
        for source in payload["discovery_sources"]
    )


def test_primary_hash_drift_is_rejected():
    payload = load_ngap_dental_reference()
    altered = copy.deepcopy(payload)
    altered["reference"]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="primary source hash mismatch"):
        validate_ngap_dental_reference(altered)


def test_conditions_hash_drift_is_rejected():
    payload = load_ngap_dental_conditions()
    altered = copy.deepcopy(payload)
    altered["reference"]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="primary source hash mismatch"):
        validate_ngap_dental_conditions(altered)


def test_provenance_hash_drift_is_rejected():
    payload = load_ngap_dental_provenance()
    altered = copy.deepcopy(payload)
    altered["locked_binary"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="locked binary hash mismatch"):
        validate_ngap_dental_provenance(altered)


def test_duplicate_or_missing_code_is_rejected():
    payload = load_ngap_dental_reference()
    altered = copy.deepcopy(payload)
    altered["acts"][-1][0] = "D815"
    with pytest.raises(ValueError, match="Duplicate NGAP dental code"):
        validate_ngap_dental_reference(altered)


def test_canonical_json_cannot_self_certify_runtime_mapping():
    payload = load_ngap_dental_reference()
    altered = copy.deepcopy(payload)
    altered["verification_status"] = "VERIFIED_PRIMARY"
    with pytest.raises(ValueError, match="Runtime certification fields are forbidden"):
        validate_ngap_dental_reference(altered)
