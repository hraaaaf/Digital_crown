"""Contract tests for the inert, versioned cephalometric norm registry."""

from types import MappingProxyType

import pytest

from backend.services.cephalo_norm_registry import (
    NormReference,
    NormRegistry,
    NormSource,
    ReferenceKind,
    SourceTier,
    registry,
)


def _primary_registry() -> NormRegistry:
    local = NormRegistry()
    local.register_source(
        NormSource(
            source_id="S1",
            tier=SourceTier.PRIMARY_ARTICLE,
            citation="Primary source",
        )
    )
    return local


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
    assert lower.mean is None and lower.sd is None
    assert lower.kind == ReferenceKind.EXTREME_RANGE
    assert lower.construction_gate == "DOWNS_MP_TANGENT"
    assert lower.active_for_patient_classification is False

    assert upper is not None
    assert upper.lower == 97.5 and upper.upper == 130.1
    assert upper.mean is None and upper.sd is None
    assert upper.construction_gate == "FH_PO_OR_V1"
    assert upper.active_for_patient_classification is False


def test_reference_keeps_population_context_explicit_and_frozen():
    ref = registry.get_reference("CRANIOM_U1_FH_EXTREMES_YOUNG_ADULT_V1")
    assert ref is not None
    assert ref.population_context["age_group"] == "young_adult"
    assert ref.population_context["occlusion"] == "Class I"
    assert ref.population_context["sample_size"] == "83"
    assert ref.population_context["orthodontic_treatment_history"] == "none"
    assert isinstance(ref.population_context, MappingProxyType)
    with pytest.raises(TypeError):
        ref.population_context["sample_size"] = "999"  # type: ignore[index]


def test_moroccan_steiner_sagittal_values_are_double_sourced_and_inert():
    source = registry.get_source("MOROCCO_STEINER_OUSEHAL_2012")
    crosscheck = registry.get_source("OUSEHAL_NUMERIC_CROSSCHECK_GOVINAKOVI_2018")
    assert source is not None
    assert source.doi == "10.1016/j.ortho.2011.12.001"
    assert source.pmid == "22236522"
    assert crosscheck is not None
    assert crosscheck.doi == "10.18295/squmj.2018.18.02.010"
    assert crosscheck.pmid == "30210848"

    expected = {
        "STEINER_SNA_CCTD_CASABLANCA_19_27_MEAN_SD_V1": (
            "STEINER_SNA_DEG_V1",
            "SNA",
            "STEINER_SNA_V1",
            80.59,
            3.80,
        ),
        "STEINER_SNB_CCTD_CASABLANCA_19_27_MEAN_SD_V1": (
            "STEINER_SNB_DEG_V1",
            "SNB",
            "STEINER_SNB_V1",
            77.68,
            3.55,
        ),
        "STEINER_ANB_CCTD_CASABLANCA_19_27_MEAN_SD_V1": (
            "STEINER_ANB_DEG_V1",
            "ANB",
            "STEINER_ANB_V1",
            3.11,
            1.68,
        ),
    }
    for reference_id, (method_id, measurement_id, construction_gate, mean, sd) in expected.items():
        ref = registry.get_reference(reference_id)
        assert ref is not None
        assert ref.method_id == method_id
        assert ref.method_version == "1"
        assert ref.measurement_id == measurement_id
        assert ref.construction_gate == construction_gate
        assert ref.kind == ReferenceKind.MEAN_SD
        assert ref.unit == "deg"
        assert ref.mean == mean and ref.sd == sd
        assert ref.lower is None and ref.upper is None
        assert ref.source_ids == (
            "MOROCCO_STEINER_OUSEHAL_2012",
            "OUSEHAL_NUMERIC_CROSSCHECK_GOVINAKOVI_2018",
        )
        assert ref.population_context["site"] == "CCTD Casablanca"
        assert ref.population_context["age_range_years"] == "19-27"
        assert ref.population_context["sample_size"] == "71"
        assert ref.population_context["sex_composition"] == "47 women; 24 men"
        assert "not universal" in ref.population_context["generalizability"]
        assert ref.active_for_patient_classification is False


def test_duplicate_source_and_reference_ids_are_rejected():
    local = _primary_registry()
    source = local.get_source("S1")
    assert source is not None
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
                kind=ReferenceKind.MEAN_SD,
                unit="deg",
                lower=None,
                upper=None,
                source_ids=("SECONDARY",),
                population_context={"sample": "test"},
                mean=10.0,
                sd=1.0,
            )
        )


def test_mean_sd_reference_is_supported_but_remains_inert():
    local = _primary_registry()
    local.register_reference(
        NormReference(
            reference_id="R-MEAN-SD",
            method_id="TEST",
            method_version="1",
            measurement_id="ANGLE",
            kind=ReferenceKind.MEAN_SD,
            unit="deg",
            lower=None,
            upper=None,
            source_ids=("S1",),
            population_context={"age_group": "young_adult", "sample_size": "71"},
            mean=82.5,
            sd=3.1,
        )
    )

    ref = local.get_reference("R-MEAN-SD")
    assert ref is not None
    assert ref.mean == 82.5
    assert ref.sd == 3.1
    assert ref.lower is None and ref.upper is None
    assert ref.active_for_patient_classification is False


@pytest.mark.parametrize(
    "mean,sd",
    [
        (None, 1.0),
        (10.0, None),
        (float("nan"), 1.0),
        (10.0, float("inf")),
        (10.0, 0.0),
        (10.0, -1.0),
    ],
)
def test_invalid_mean_sd_values_are_rejected(mean, sd):
    local = _primary_registry()
    with pytest.raises(ValueError):
        local.register_reference(
            NormReference(
                reference_id="R-MEAN-SD",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.MEAN_SD,
                unit="deg",
                lower=None,
                upper=None,
                source_ids=("S1",),
                population_context={"sample": "test"},
                mean=mean,
                sd=sd,
            )
        )


def test_reference_kinds_reject_mixed_numeric_shapes():
    local = _primary_registry()
    with pytest.raises(ValueError, match="EXTREME_RANGE cannot define mean or sd"):
        local.register_reference(
            NormReference(
                reference_id="R-RANGE",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.EXTREME_RANGE,
                unit="deg",
                lower=1.0,
                upper=2.0,
                source_ids=("S1",),
                population_context={"sample": "test"},
                mean=1.5,
                sd=0.25,
            )
        )
    with pytest.raises(ValueError, match="MEAN_SD cannot define lower or upper"):
        local.register_reference(
            NormReference(
                reference_id="R-MEAN-SD",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.MEAN_SD,
                unit="deg",
                lower=1.0,
                upper=2.0,
                source_ids=("S1",),
                population_context={"sample": "test"},
                mean=1.5,
                sd=0.25,
            )
        )


def test_percentile_kind_remains_fail_closed():
    local = _primary_registry()
    with pytest.raises(ValueError, match="EXTREME_RANGE and MEAN_SD"):
        local.register_reference(
            NormReference(
                reference_id="R-PERCENTILE",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.PERCENTILE,
                unit="deg",
                lower=1.0,
                upper=2.0,
                source_ids=("S1",),
                population_context={"sample": "test"},
            )
        )


@pytest.mark.parametrize(
    "lower,upper",
    [(None, 2.0), (1.0, None), (3.0, 2.0), (float("nan"), 2.0), (1.0, float("inf"))],
)
def test_invalid_ranges_are_rejected(lower, upper):
    local = _primary_registry()
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


def test_empty_population_context_is_rejected():
    local = _primary_registry()
    with pytest.raises(ValueError, match="explicit population context"):
        local.register_reference(
            NormReference(
                reference_id="R1",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.MEAN_SD,
                unit="deg",
                lower=None,
                upper=None,
                source_ids=("S1",),
                population_context={},
                mean=10.0,
                sd=1.0,
            )
        )


def test_direct_activation_for_patient_classification_is_forbidden():
    local = _primary_registry()
    with pytest.raises(ValueError, match="does not permit direct activation"):
        local.register_reference(
            NormReference(
                reference_id="R1",
                method_id="TEST",
                method_version="1",
                measurement_id="ANGLE",
                kind=ReferenceKind.MEAN_SD,
                unit="deg",
                lower=None,
                upper=None,
                source_ids=("S1",),
                population_context={"sample": "test"},
                mean=10.0,
                sd=1.0,
                active_for_patient_classification=True,
            )
        )
