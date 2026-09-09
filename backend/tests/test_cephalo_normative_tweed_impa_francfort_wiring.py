"""Geometry-only regression contract for Tweed / IMPA / I-Francfort.

The cephalometric engine must expose raw measurements only. It must not route
those values through normative interpretation, diagnostic labels, syntheses,
or treatment strategy generation.
"""

import pytest

from backend.services.cephalo_engine import CephaloEngine


POINTS_ALL_MEASURES = {
    "S": (50.0, 60.0), "N": (70.0, 40.0), "Po": (40.0, 40.0), "Or": (80.0, 40.0),
    "A": (95.0, 90.0), "B": (60.0, 130.0), "Go": (60.0, 150.0), "Me": (85.0, 170.0),
    "U1i": (100.0, 100.0), "U1a": (105.0, 80.0), "L1i": (92.0, 120.0), "L1a": (88.0, 140.0),
    "Prn": (100.0, 40.0), "Pog_soft": (100.0, 200.0), "Ls": (92.0, 100.0),
    "Li": (108.0, 120.0), "Sn": (100.0, 60.0), "Occ_Ant": (110.0, 110.0),
    "Occ_Post": (60.0, 110.0), "Co": (45.0, 50.0), "Gn": (90.0, 165.0), "ANS": (85.0, 75.0),
}


def _values(result):
    return (
        result.metrics.analyse_osseuse.Angle_de_Tweed.valeur,
        result.metrics.analyse_dentaire.IMPA.valeur,
        result.metrics.analyse_dentaire.I_Francfort.valeur,
    )


def test_raw_tweed_impa_francfort_values_are_present_and_finite():
    result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES)
    assert all(value is not None for value in _values(result))
    assert all(value == pytest.approx(float(value)) for value in _values(result))


def test_raw_geometry_is_independent_of_age_and_sex_context():
    engine = CephaloEngine(mm_per_pixel=0.5)
    baseline = _values(engine.calculate_metrics(POINTS_ALL_MEASURES, age=None, sex=None))
    male = _values(engine.calculate_metrics(POINTS_ALL_MEASURES, age=30, sex="M"))
    female = _values(engine.calculate_metrics(POINTS_ALL_MEASURES, age=30, sex="F"))
    assert male == pytest.approx(baseline)
    assert female == pytest.approx(baseline)


def test_engine_emits_no_diagnostic_or_treatment_narrative():
    result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS_ALL_MEASURES, age=30, sex="F")
    assert result.ai_narrative == {}
