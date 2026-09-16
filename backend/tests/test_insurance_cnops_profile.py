from backend.services.insurance_cnops_dental_profile import (
    CNOPS_DENTAL_MAX_LINES,
    CNOPS_DENTAL_PROFILE,
    CNOPS_DENTAL_PROFILE_VERSION,
    CNOPS_DENTAL_TEMPLATE_SHA256,
    CNOPS_DENTAL_TEMPLATE_VERSION,
)


def test_cnops_profile_is_bound_to_exact_cabinet_validated_binary():
    assert CNOPS_DENTAL_TEMPLATE_SHA256 == (
        "89097caca32aef6b4d34d2d06fb9cc6f9bdc1f3c4385cf5558b5742a3af6f505"
    )
    assert CNOPS_DENTAL_TEMPLATE_VERSION == "CNOPS-DENTAL-CABINET-2026-09-16"
    assert CNOPS_DENTAL_PROFILE.organization == "CNOPS"
    assert CNOPS_DENTAL_PROFILE.template_version == CNOPS_DENTAL_TEMPLATE_VERSION
    assert CNOPS_DENTAL_PROFILE.template_hash == CNOPS_DENTAL_TEMPLATE_SHA256
    assert CNOPS_DENTAL_PROFILE.profile_version == CNOPS_DENTAL_PROFILE_VERSION
    assert CNOPS_DENTAL_PROFILE.max_lines == 9 == CNOPS_DENTAL_MAX_LINES


def test_cnops_profile_never_targets_signature_stamp_insurer_or_agent_zones():
    keys = {placement.field_key for placement in CNOPS_DENTAL_PROFILE.placements}
    forbidden_tokens = ("signature", "cachet", "stamp", "insurer", "mutuelle", "agent")
    assert not any(
        token in key.lower()
        for key in keys
        for token in forbidden_tokens
    )

    # Page 1 declaration fields end before the signature/mutuelle/agent boxes.
    page_one = [p for p in CNOPS_DENTAL_PROFILE.placements if p.page_index == 0]
    assert page_one
    assert max(p.y for p in page_one) <= 452

    # Page 2 signature/cachet column begins to the right of the amount column.
    page_two = [p for p in CNOPS_DENTAL_PROFILE.placements if p.page_index == 1]
    assert page_two
    assert max(p.x for p in page_two) < 728.5


def test_cnops_profile_matches_exact_visible_form_fields():
    keys = {placement.field_key for placement in CNOPS_DENTAL_PROFILE.placements}
    assert "administrative.insured_affiliation_number" in keys
    assert "administrative.insured_registration_number" in keys
    assert "administrative.insured_quality" not in keys
    assert "administrative.practitioner_full_name" not in keys

    assert "choice.relationship_to_insured.CONJOINT" in keys
    assert "choice.relationship_to_insured.ENFANT" in keys
    assert "choice.request_nature.PRIOR_APPROVAL" in keys
    assert "choice.request_nature.EXECUTION" in keys

    # There are exactly nine dental rows and no invented key-value field.
    for index in range(9):
        assert f"lines[{index}].teeth" in keys
        assert f"lines[{index}].ngap_code" in keys
        assert f"lines[{index}].service_date" in keys
        assert f"lines[{index}].ngap_coefficient" in keys
        assert f"lines[{index}].amount_mad" in keys
    assert not any("key_value" in key for key in keys)
    assert not any(key.startswith("lines[9].") for key in keys)
