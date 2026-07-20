from backend.services.cephalo_engine import CephaloEngine


POINTS = {
    "S": (50.0, 60.0), "N": (70.0, 40.0), "Po": (40.0, 40.0), "Or": (80.0, 40.0),
    "A": (90.0, 90.0), "B": (85.0, 130.0), "Go": (60.0, 150.0), "Me": (85.0, 170.0),
    "U1i": (100.0, 100.0), "U1a": (105.0, 80.0), "L1i": (92.0, 120.0), "L1a": (88.0, 140.0),
    "Prn": (100.0, 40.0), "Pog_soft": (100.0, 200.0), "Ls": (92.0, 100.0),
    "Li": (108.0, 120.0), "Sn": (100.0, 60.0), "Occ_Ant": (110.0, 110.0),
    "Occ_Post": (60.0, 110.0), "Co": (45.0, 50.0), "Gn": (90.0, 165.0), "ANS": (85.0, 75.0),
}


def test_engine_without_calibration_keeps_angles_and_omits_mm_metrics():
    result = CephaloEngine(mm_per_pixel=None).calculate_metrics(POINTS)
    dental = result.metrics.analyse_dentaire
    skeletal = result.metrics.analyse_osseuse
    esthetic = result.metrics.analyse_esthetique

    assert result.analysis_metadata.pixel_ratio is None
    assert skeletal.SNA.valeur is not None
    assert skeletal.SNB.valeur is not None
    assert skeletal.ANB.valeur is not None
    assert dental.IMPA.valeur is not None
    assert dental.I_Francfort.valeur is not None
    assert dental.Inter_Incisif.valeur is not None
    assert skeletal.Angle_de_Tweed.valeur is not None
    assert esthetic.Angle_Nasolabial.valeur is not None

    assert dental.Surplomb.valeur is None
    assert dental.Recouvrement.valeur is None
    assert skeletal.Situation_A.valeur is None
    assert skeletal.Situation_B.valeur is None
    assert skeletal.Decalage_A_B.valeur is None
    assert esthetic.Ligne_E_Ls.valeur is None
    assert esthetic.Ligne_E_Li.valeur is None
    assert "millimètres" in result.ai_narrative["diagnostic_squelettique"]
    assert "A'B': 2.3 mm" not in result.ai_narrative["diagnostic_squelettique"]


def test_engine_with_calibration_still_calculates_mm_metrics():
    result = CephaloEngine(mm_per_pixel=0.5).calculate_metrics(POINTS)
    dental = result.metrics.analyse_dentaire
    skeletal = result.metrics.analyse_osseuse
    esthetic = result.metrics.analyse_esthetique

    assert result.analysis_metadata.pixel_ratio == 0.5
    assert dental.Surplomb.valeur is not None
    assert dental.Recouvrement.valeur is not None
    assert skeletal.Situation_A.valeur is not None
    assert skeletal.Situation_B.valeur is not None
    assert skeletal.Decalage_A_B.valeur is not None
    assert esthetic.Ligne_E_Ls.valeur is not None
    assert esthetic.Ligne_E_Li.valeur is not None