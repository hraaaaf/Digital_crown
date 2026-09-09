"""
Tests unitaires purs pour CephaloConsistencyValidator et cephalo_measure_registry.
Aucune connexion DB. Exécuter avec : pytest backend/tests/test_cephalo_validator.py -v
"""
from backend.services.cephalo_measure_registry import is_mm_metric, cephalo_unit
from backend.services.cephalo_consistency_validator import cephalo_consistency_validator

DEGREE_SYMBOL = "°"


class TestCephaloMeasureRegistry:
    def test_mm_keywords_detected(self):
        for name in ["Surplomb", "Recouvrement", "Wits", "I_NA_mm", "I_NB_mm", "Ligne_E"]:
            assert is_mm_metric(name), f"{name} should be detected as mm"

    def test_angle_keywords_not_mm(self):
        for name in ["SNA", "SNB", "ANB", "Inter_Incisif", "IMPA", "Angle_Nasolabial", "I_Francfort"]:
            assert not is_mm_metric(name), f"{name} should not be detected as mm"

    def test_cephalo_unit_mm(self):
        assert cephalo_unit("Surplomb") == "mm"
        assert cephalo_unit("Wits") == "mm"
        assert cephalo_unit("I_NB_mm") == "mm"

    def test_cephalo_unit_degrees(self):
        assert cephalo_unit("SNA") == DEGREE_SYMBOL
        assert cephalo_unit("ANB") == DEGREE_SYMBOL
        assert cephalo_unit("IMPA") == DEGREE_SYMBOL


def _make_data(**sections):
    return {"metrics": sections}


def _angle(val, unite=DEGREE_SYMBOL):
    return {"valeur": val, "unite": unite}


def _mm(val, unite="mm"):
    return {"valeur": val, "unite": unite}


class TestStructuralConsistency:
    v = cephalo_consistency_validator

    def test_consistent_sna_snb_anb_clean(self):
        data = _make_data(analyse_osseuse={
            "SNA": _angle(82), "SNB": _angle(80), "ANB": _angle(2),
        })
        r = self.v.validate(data)
        assert not r.fatals
        assert not r.warnings

    def test_sna_snb_anb_internal_incoherence_fatal(self):
        data = _make_data(analyse_osseuse={
            "SNA": _angle(83), "SNB": _angle(80), "ANB": _angle(8),
        })
        r = self.v.validate(data)
        assert any("Incoh" in f for f in r.fatals)

    def test_high_or_low_values_are_not_clinically_classified(self):
        data = _make_data(
            analyse_osseuse={
                "SNA": _angle(110),
                "Wits": _mm(20.0),
            },
            analyse_dentaire={
                "Surplomb": _mm(6.0),
                "Recouvrement": _mm(15.0),
            },
            analyse_esthetique={"Angle_Nasolabial": _angle(170)},
        )
        r = self.v.validate(data)
        assert r.is_valid
        assert not r.fatals
        assert not r.warnings

    def test_no_class_ii_or_iii_contradiction_rule(self):
        data = _make_data(analyse_osseuse={
            "SNA": _angle(78), "SNB": _angle(82), "ANB": _angle(-4),
        })
        r = self.v.validate(data)
        assert r.is_valid
        assert not any("Classe" in message or "Contradiction" in message for message in r.fatals + r.warnings)


class TestUnitContradictions:
    v = cephalo_consistency_validator

    def test_recouvrement_tagged_degrees_fatal(self):
        data = _make_data(analyse_dentaire={
            "Recouvrement": {"valeur": 2.0, "unite": DEGREE_SYMBOL}
        })
        r = self.v.validate(data)
        assert any("Recouvrement" in f for f in r.fatals)

    def test_surplomb_tagged_degrees_fatal(self):
        data = _make_data(analyse_dentaire={
            "Surplomb": {"valeur": 3.0, "unite": DEGREE_SYMBOL}
        })
        r = self.v.validate(data)
        assert any("Surplomb" in f for f in r.fatals)

    def test_angle_tagged_correctly_no_error(self):
        data = _make_data(analyse_osseuse={
            "SNA": {"valeur": 82.0, "unite": DEGREE_SYMBOL},
            "Wits": {"valeur": 1.0, "unite": "mm"},
        })
        r = self.v.validate(data)
        assert not r.fatals
        assert not r.warnings

    def test_missing_angles_data_fatal(self):
        r = cephalo_consistency_validator.validate(None)
        assert r.fatals
        assert not r.is_valid


class TestCalibrationStatusWarning:
    v = cephalo_consistency_validator

    def test_unverified_calibration_produces_warning(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(82)})
        data["calibration_status"] = "unverified"
        r = self.v.validate(data)
        assert any("Calibration non v" in w for w in r.warnings)
        assert r.is_valid

    def test_verified_calibration_no_warning(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(82)})
        data["calibration_status"] = "verified"
        r = self.v.validate(data)
        assert not any("Calibration non v" in w for w in r.warnings)

    def test_missing_calibration_status_no_warning(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(82)})
        r = self.v.validate(data)
        assert not any("Calibration non v" in w for w in r.warnings)
