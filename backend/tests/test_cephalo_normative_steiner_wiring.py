"""Regression contract for the geometry-only cephalometric core.

The former Steiner wiring tests asserted that runtime engines consumed the
normative service and could propagate an authoritative diagnosis/treatment.
That architecture was intentionally removed. Runtime cephalometry now computes
patient-observed geometry only; normative evaluation remains isolated and
fail-closed.
"""

import math

import pytest

from backend.schemas.cephalo_normative import NormativeContext
from backend.services.cephalo_engine import CephaloEngine
from backend.services.cephalo_normative_service import (
    NormativeEvaluationStatus,
    evaluate_measurement,
)


POINTS_STRONG_ANB = {
    "S": (50.0, 60.0), "N": (70.0, 40.0), "Po": (40.0, 40.0), "Or": (80.0, 40.0),
    "A": (95.0, 90.0), "B": (60.0, 130.0), "Go": (60.0, 150.0), "Me": (85.0, 170.0),
    "U1i": (100.0, 100.0), "U1a": (105.0, 80.0), "L1i": (92.0, 120.0), "L1a": (88.0, 140.0),
    "Prn": (100.0, 40.0), "Pog_soft": (100.0, 200.0), "Ls": (92.0, 100.0),
    "Li": (108.0, 120.0), "Sn": (100.0, 60.0), "Occ_Ant": (110.0, 110.0),
    "Occ_Post": (60.0, 110.0), "Co": (45.0, 50.0), "Gn": (90.0, 165.0), "ANS": (85.0, 75.0),
}


def _skeletal_values(*, age=None, sex=None):
    result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(
        POINTS_STRONG_ANB,
        age=age,
        sex=sex,
    )
    skeletal = result.metrics.analyse_osseuse
    return result, (skeletal.SNA.valeur, skeletal.SNB.valeur, skeletal.ANB.valeur)


class TestGeometryOnlyContract:
    def test_raw_sna_snb_anb_are_repeatable_and_finite(self):
        result1, values1 = _skeletal_values(age=30, sex="M")
        result2, values2 = _skeletal_values(age=30, sex="M")

        assert values1 == values2
        assert all(value is not None and math.isfinite(value) for value in values1)
        assert values1[2] == pytest.approx(values1[0] - values1[1], abs=0.15)
        assert result1.ai_narrative == {}
        assert result2.ai_narrative == {}

    @pytest.mark.parametrize(
        "age,sex",
        [
            (None, None),
            (10, "F"),
            (30, "M"),
            (70, "AUTRE"),
        ],
    )
    def test_age_and_sex_do_not_change_geometry(self, age, sex):
        _, baseline = _skeletal_values(age=None, sex=None)
        result, candidate = _skeletal_values(age=age, sex=sex)

        assert candidate == baseline
        assert result.ai_narrative == {}

    def test_runtime_engine_has_no_normative_wiring(self):
        import backend.services.cephalo_engine as engine_module

        assert not hasattr(engine_module, "evaluate_measurement")
        source = engine_module.__file__
        assert source


class TestNormativeServiceRemainsIsolatedFailClosed:
    @pytest.mark.parametrize(
        "measurement_id",
        ["Wits_Appraisal", "Angle_Nasolabial", "Situation_B", "Decalage_A_B"],
    )
    def test_quarantined_measurements_remain_blocked(self, measurement_id):
        result = evaluate_measurement(measurement_id, 0.0, "v1", NormativeContext())

        assert result.status == NormativeEvaluationStatus.DEFINITION_QUARANTINED
        assert result.classification is None
