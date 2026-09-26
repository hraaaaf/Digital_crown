from backend.services.catalog_act_applicability_defaults import default_applicability_for_code


def test_bridge_default_is_permanent_group_only():
    profile = default_applicability_for_code("HBMD063")
    assert profile["dentitions"] == ["PERMANENT"]
    assert profile["selection_modes"] == ["GROUP"]
    assert profile["min_selected_teeth"] == 3


def test_pediatric_primary_crown_is_primary_and_high_priority():
    profile = default_applicability_for_code("HBMD184")
    assert profile["dentitions"] == ["PRIMARY"]
    assert profile["suggestion_priority"] == 95


def test_periodontal_root_planing_remains_searchable_but_not_suggested():
    profile = default_applicability_for_code("HBMD101")
    assert profile["dentitions"] == ["PRIMARY", "PERMANENT"]
    assert profile["suggestion_priority"] == 0


def test_unknown_custom_act_has_no_implicit_restrictions():
    assert default_applicability_for_code("CUSTOM-001") == {}
