from backend.schemas.catalog import CatalogActCreate


def test_catalog_act_applicability_is_backward_compatible():
    payload = CatalogActCreate(name="Acte libre", base_price=100)
    assert payload.applicability.suggestion_priority == 0
    assert payload.applicability.searchable_when_not_suggested is True
    assert payload.applicability.dentitions == []


def test_catalog_act_applicability_validates_configurable_rules():
    payload = CatalogActCreate(
        name="Bridge",
        base_price=1000,
        applicability={
            "dentitions": ["PERMANENT"],
            "selection_modes": ["GROUP"],
            "treatment_areas": ["TOOTH_RANGE"],
            "min_selected_teeth": 3,
            "suggestion_priority": 90,
        },
    )
    assert payload.applicability.dentitions == ["PERMANENT"]
    assert payload.applicability.min_selected_teeth == 3
    assert payload.applicability.suggestion_priority == 90
