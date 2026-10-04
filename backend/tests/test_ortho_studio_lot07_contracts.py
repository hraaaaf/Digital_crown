import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "docs" / "audits" / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_case_record_contract_separates_clinical_photo_set_from_reconstruction_subset():
    contract = _load("ortho_case_record_contract_v1.json")
    photos = contract["photo_protocol"]
    extraoral = photos["extraoral"]
    intraoral = photos["intraoral"]
    reconstruction = photos["photo_reconstruction_input"]

    assert len(extraoral) == 3
    assert len(intraoral) == 5
    assert len(set(extraoral + intraoral)) == 8
    assert set(reconstruction) == set(intraoral)


def test_case_record_contract_rejects_browser_storage_as_canonical_record():
    contract = _load("ortho_case_record_contract_v1.json")
    policy = contract["storage_policy"]
    assert policy["patient_media"] == "LOCAL_PATIENT_RECORD"
    assert policy["browser_local_storage"] == "FORBIDDEN_AS_CANONICAL_RECORD"
def test_case_record_contract_fails_closed_for_photo_metric_authority():
    contract = _load("ortho_case_record_contract_v1.json")
    authority = contract["authority_rules"]

    assert authority["PHOTO_RECONSTRUCTION"] == (
        "RND_NON_MEASUREMENT_AUTHORITATIVE_UNTIL_VALIDATED"
    )
    assert authority["photo_direct_mm"] == (
        "FAIL_CLOSED_UNLESS_METHOD_SPECIFIC_VALIDATION"
    )


def test_case_record_contract_requires_provenance_and_timepoint():
    contract = _load("ortho_case_record_contract_v1.json")
    required = set(contract["provenance_required"])
    assert {
        "source_type",
        "acquired_at",
        "operator_or_device",
        "patient_record_id",
        "timepoint_id",
    } <= required
    assert contract["timepoint_contract"]["longitudinal_registration"] == "EXTERNAL_TO_LOT07"


def test_structure_contract_keeps_display_geometry_non_authoritative():
    contract = _load("cephalo_anatomical_structure_contract_v1.json")
    classes = contract["structure_classes"]

    assert classes["HARD_TISSUE_CONTOUR"]["default_authority"] == "DISPLAY_TEMPLATE_ONLY"
    assert classes["SOFT_TISSUE_PROFILE"]["default_authority"] == "DISPLAY_TEMPLATE_ONLY"
    assert classes["TOOTH_TEMPLATE"]["default_authority"] == "DISPLAY_TEMPLATE_ONLY"
def test_structure_contract_preserves_lot06_scientific_authority():
    contract = _load("cephalo_anatomical_structure_contract_v1.json")

    assert contract["scientific_authority"] == "LOT06_CANONICAL_ENGINE"
    assert "LOT07_DOES_NOT_DEFINE_NEW_CEPHALOMETRIC_FORMULAS" in contract["invariants"]
    assert (
        "DISPLAY_TEMPLATE_ONLY_NEVER_DRIVES_MEASUREMENTS"
        in contract["invariants"]
    )


def test_structure_contract_requires_extra_fields_for_authoritative_geometry():
    contract = _load("cephalo_anatomical_structure_contract_v1.json")
    required = set(contract["measurement_authoritative_extra_fields"])

    assert {
        "canonical_dependency_ids",
        "source_contracts",
        "availability_gate",
    } == required


def test_lot07_default_contours_are_all_display_only():
    contract = _load("cephalo_anatomical_structure_contract_v1.json")
    defaults = contract["lot07_default_structures"]

    assert defaults
    assert len({item["structure_id"] for item in defaults}) == len(defaults)
    assert all(
        item["authority_state"] == "DISPLAY_TEMPLATE_ONLY"
        for item in defaults
    )


def test_legacy_photo_slots_fail_closed_when_mapping_is_ambiguous():
    contract = _load("ortho_case_record_contract_v1.json")
    migration = contract["legacy_slot_migration"]

    assert migration["intra_profile"] == "AMBIGUOUS_FAIL_CLOSED_NO_AUTO_MAP"
    assert migration["moulage_max"] == "LEGACY_IMAGE_ONLY_NOT_DENTAL_MODEL_RECORD"
    assert migration["moulage_mand"] == "LEGACY_IMAGE_ONLY_NOT_DENTAL_MODEL_RECORD"


def test_landmarks_are_candidate_inputs_until_promoted_through_canonical_path():
    contract = _load("cephalo_anatomical_structure_contract_v1.json")
    landmark = contract["structure_classes"]["LANDMARK"]

    assert landmark["default_authority"] == "CANDIDATE_INPUT"
    assert landmark["promotion_gate"] == "AUDITED_CANONICAL_INPUT_PATH"


def test_model_records_require_metric_coordinate_and_integrity_metadata():
    contract = _load("ortho_case_record_contract_v1.json")
    model = contract["record_types"]["dental_model"]

    assert model["allowed_units"] == ["mm"]
    assert {
        "unit",
        "coordinate_space",
        "orientation_state",
        "source_type",
        "checksum",
    } == set(model["required_metadata"])
    assert contract["photo_protocol"]["photo_reconstruction_gate"] == (
        "ALL_5_STANDARDIZED_VIEWS_REQUIRED"
    )


def test_canonical_construction_requires_authoritative_inputs():
    contract = _load("cephalo_anatomical_structure_contract_v1.json")
    construction = contract["structure_classes"]["CANONICAL_CONSTRUCTION"]

    assert construction["default_authority"] == "MEASUREMENT_AUTHORITATIVE"
    assert construction["input_gate"] == "ALL_CANONICAL_INPUTS_MEASUREMENT_AUTHORITATIVE"
