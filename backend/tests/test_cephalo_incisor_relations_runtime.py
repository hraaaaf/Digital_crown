from backend.services.cephalo_engine import CephaloEngine


def _base_points(upper_x: float, upper_y: float, lower_x: float, lower_y: float):
    return {
        "Po": (0.0, 0.0),
        "Or": (100.0, 0.0),
        "U1_incisal": (upper_x, upper_y),
        "L1_incisal": (lower_x, lower_y),
    }


def test_backend_preserves_signed_overjet_direction():
    engine = CephaloEngine(mm_per_pixel=1.0)

    positive = engine.calculate_metrics(_base_points(60.0, 20.0, 50.0, 20.0))
    reverse = engine.calculate_metrics(_base_points(40.0, 20.0, 50.0, 20.0))

    assert positive.metrics.analyse_dentaire.Surplomb.valeur == 10.0
    assert reverse.metrics.analyse_dentaire.Surplomb.valeur == -10.0


def test_backend_preserves_signed_overbite_and_fails_closed_without_calibration():
    engine = CephaloEngine(mm_per_pixel=1.0)
    overlap = engine.calculate_metrics(_base_points(50.0, 30.0, 50.0, 20.0))
    open_bite = engine.calculate_metrics(_base_points(50.0, 10.0, 50.0, 20.0))
    uncalibrated = CephaloEngine(mm_per_pixel=None).calculate_metrics(
        _base_points(60.0, 30.0, 50.0, 20.0)
    )

    assert overlap.metrics.analyse_dentaire.Recouvrement.valeur == 10.0
    assert open_bite.metrics.analyse_dentaire.Recouvrement.valeur == -10.0
    assert uncalibrated.metrics.analyse_dentaire.Surplomb.valeur is None
    assert uncalibrated.metrics.analyse_dentaire.Recouvrement.valeur is None
