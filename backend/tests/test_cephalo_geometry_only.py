"""Regression tests for the geometry-only cephalometric core."""

from backend.services.cephalo_engine import CephaloEngine


def _points():
    return {
        "S": (10.0, 10.0),
        "N": (20.0, 10.0),
        "Po": (0.0, 20.0),
        "Or": (20.0, 20.0),
        "A": (24.0, 28.0),
        "B": (22.0, 38.0),
        "Go": (5.0, 50.0),
        "Me": (25.0, 55.0),
        "U1a": (20.0, 25.0),
        "U1i": (24.0, 35.0),
        "L1a": (20.0, 48.0),
        "L1i": (23.0, 38.0),
        "Prn": (35.0, 25.0),
        "Pog_soft": (30.0, 50.0),
        "Ls": (33.0, 34.0),
        "Li": (32.0, 39.0),
    }


def test_geometry_core_keeps_normative_metadata_empty():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(
        _points(), age=9, sex="M", cvm_stage="CS3"
    )

    for group in (
        result.metrics.analyse_dentaire,
        result.metrics.analyse_osseuse,
        result.metrics.analyse_esthetique,
    ):
        for measure in group.model_dump().values():
            assert measure["norm_mean"] is None
            assert measure["norm_min"] is None
            assert measure["norm_max"] is None
            assert measure["z_score"] is None
            assert measure["status"] == "N/A"


def test_geometry_core_never_emits_growth_or_treatment():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(
        _points(), age=9, sex="F", cvm_stage="CS2"
    )

    assert result.t1_projection == {}
    assert result.t2_projection == {}
    assert result.ai_narrative == {}
    assert result.ai_diagnostic is None
    assert result.clinical_data.ddm_reelle is None
    assert result.clinical_data.plan_traitement == ""


def test_geometry_core_does_not_infer_patient_cohort_from_age():
    child = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(), age=9)
    adult = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points(), age=35)

    assert child.analysis_metadata.cohort == "Non classé"
    assert adult.analysis_metadata.cohort == "Non classé"


def test_geometry_core_still_computes_raw_patient_measurements():
    result = CephaloEngine(mm_per_pixel=0.2).calculate_metrics(_points())

    assert result.metrics.analyse_dentaire.IMPA.valeur is not None
    assert result.metrics.analyse_dentaire.I_Francfort.valeur is not None
    assert result.metrics.analyse_osseuse.SNA.valeur is not None
    assert result.metrics.analyse_osseuse.SNB.valeur is not None
    assert result.metrics.analyse_osseuse.ANB.valeur is not None
    assert result.metrics.analyse_esthetique.Ligne_E_Ls.valeur is not None
