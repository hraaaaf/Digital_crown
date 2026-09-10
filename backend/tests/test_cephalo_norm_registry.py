"""Contract tests for the inert, versioned cephalometric norm registry."""

import pytest

from backend.services.cephalo_norm_registry import (
    NormReference,
    NormRegistry,
    NormSource,
    ReferenceKind,
    SourceTier,
    registry,
)


def test_craniom_primary_sources_are_versioned_and_traceable():
    part1 = registry.get_source("CRANIOM_PART1_2010")
    part2 = registry.get_source("CRANIOM_PART2_2011")
    assert part1 is not None and part1.doi == "10.1051/odfen/2010406"
    assert part2 is not None and part2.doi == "10.1051/odfen/2011104"
    assert part1.tier == SourceTier.PRIMARY_ARTICLE
    assert part2.tier == SourceTier.PRIMARY_ARTICLE


def test_exact_craniom_extreme_ranges_are_preserved_but_inactive():
    lower = registry.get_reference("CRANIOM_L1_DOWNS_MP_EXTREMES_YOUNG_ADULT_V1")
    upper = registry.get_reference("CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1")

    assert lower is not None
    assert lower.lower == 78.0 and lower.upper == 114.0
    assert lower.kind == ReferenceKind.EXTREME_RANGE
    assert lower.construction_gate == "DOWNS_MP_TANGENT"
    assert lower.active_for_patient_classification is False

    assert upper is not None
    assert upper.lower == 97.5 and upper.upper == 130.1
    assert upper.construction_gate == "FH_PO_OR_V1"
    assert upper.active_for_patient_classification is False


def test_reference_keeps_population_context_explicit():
    ref = registry.get_reference("CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1")
    assert ref is not None
    assert ref.population_context["age_group"] == "young_adult"
    assert ref.population_context["occlusion"] == "Class I"
    assert ref.population_context["sample_size"] == "83"
    assert ref.population_context["orthodontic_treatment_history"] == "none"


def test_moroccan_source_is_registered_without_unverified_numeric_reference():
    source = registry.get_source("MOROCCO_STEINER_OUSEHAL_2012")
    assert source is not None
    assert source.doi == "10.1016/j.ortho.2011.12.001"
    assert source.pmid == "22236522"
    assert not any(
        "MOROCCO" in ref.reference_id for ref in registry.references.values()
    )


def test_duplicate_source_and_reference_ids_are_rejected():
    local = NormRegistry()
    source = NormSource(
        source_id="S1",
        tier=SourceTier.PRIMARY_ARTICLE,
        citation="Primary source",
    )
    local.register_source(source)
    with pytest.raises(ValueError, match="Duplicate normative source"):
        local.register_source(source)

    ref = NormReference(
        reference_id="R1",
        method_id="TEST",
        method_version="1",
        measurement_id="ANGLE",
        kind=ReferenceKind.EXTREME_RANGE,
        unit="deg",
        lower=1.0,
        upper=2.0,
        source_ids=("S1",),
        population_context={"sample": "test"},
    )
    local.register_reference(ref)
    with pytest.raises(ValueError, match="Duplicate normative reference"):
        local.register_reference(ref)


def test_unknown_source_is_rejected():
    local = NormRegistry()
    with pytest.raises(ValueError, match="Unknown normative source"):
        local.register_reference(
            NormReference(
                reference_id="R1",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.EXTREME_RANGE,
                unit="deg",
                lower=1.0,
                upper=2.0,
                source_ids=("missing",),
                population_context={"sample": "test"},
            )
        )


def test_secondary_only_numeric_reference_is_rejected():
    local = NormRegistry()
    local.register_source(
        NormSource(
            source_id="SECONDARY",
            tier=SourceTier.SECONDARY_TECHNICAL,
            citation="Secondary technical reproduction",
        )
    )
    with pytest.raises(ValueError, match="primary research source"):
        local.register_reference(
            NormReference(
                reference_id="R1",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.EXTREME_RANGE,
                unit="deg",
                lower=1.0,
                upper=2.0,
                source_ids=("SECONDARY",),
                population_context={"sample": "test"},
            )
        )


@pytest.mark.parametrize(
    "lower,upper",
    [(3.0, 2.0), (float("nan"), 2.0), (1.0, float("inf"))],
)
def test_invalid_ranges_are_rejected(lower, upper):
    local = NormRegistry()
    local.register_source(
        NormSource(
            source_id="S1",
            tier=SourceTier.PRIMARY_ARTICLE,
            citation="Primary source",
        )
    )
    with pytest.raises(ValueError):
        local.register_reference(
            NormReference(
                reference_id="R1",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.EXTREME_RANGE,
                unit="deg",
                lower=lower,
                upper=upper,
                source_ids=("S1",),
                population_context={"sample": "test"},
            )
        )


def test_direct_activation_for_patient_classification_is_forbidden():
    local = NormRegistry()
    local.register_source(
        NormSource(
            source_id="S1",
            tier=SourceTier.PRIMARY_ARTICLE,
            citation="Primary source",
        )
    )
    with pytest.raises(ValueError, match="does not permit direct activation"):
        local.register_reference(
            NormReference(
                reference_id="R1",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.EXTREME_RANGE,
                unit="deg",
                lower=1.0,
                upper=2.0,
                source_ids=("S1",),
                population_context={"sample": "test"},
                active_for_patient_classification=True,
            )
        )
