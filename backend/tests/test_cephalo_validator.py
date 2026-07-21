"""
Tests unitaires purs pour CephaloConsistencyValidator et cephalo_measure_registry.
Aucune connexion DB. Exécuter avec : pytest backend/tests/test_cephalo_validator.py -v
"""
import pytest
from backend.services.cephalo_measure_registry import is_mm_metric, cephalo_unit
from backend.services.cephalo_consistency_validator import (
    CephaloConsistencyValidator,
    cephalo_consistency_validator,
)

DEGREE_SYMBOL = "°"


# ── Registry ──────────────────────────────────────────────────────────────────

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


# ── Validator helpers ─────────────────────────────────────────────────────────

def _make_data(**sections):
    return {"metrics": sections}

def _angle(val, unite=DEGREE_SYMBOL):
    return {"valeur": val, "unite": unite}

def _mm(val, unite="mm"):
    return {"valeur": val, "unite": unite}


# ── Angle bounds ──────────────────────────────────────────────────────────────

class TestAngleBounds:
    v = cephalo_consistency_validator

    def test_normal_angles_clean(self):
        data = _make_data(analyse_osseuse={
            "SNA": _angle(82), "SNB": _angle(80), "ANB": _angle(2),
        })
        r = self.v.validate(data)
        assert not r.fatals
        assert not r.warnings

    def test_sna_out_of_physio_fatal(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(110)})
        r = self.v.validate(data)
        assert any("SNA" in f for f in r.fatals)

    def test_anb_out_of_soft_warning(self):
        data = _make_data(analyse_osseuse={
            "SNA": _angle(84), "SNB": _angle(77), "ANB": _angle(7),
        })
        r = self.v.validate(data)
        assert r.is_valid
        assert any("ANB" in w for w in r.warnings)

    def test_sna_snb_anb_internal_incoherence_fatal(self):
        # SNA - SNB = 3 but ANB = 8 → delta > 1.5°
        data = _make_data(analyse_osseuse={
            "SNA": _angle(83), "SNB": _angle(80), "ANB": _angle(8),
        })
        r = self.v.validate(data)
        assert any("Incoh" in f for f in r.fatals)

    def test_class_contradiction_fatal(self):
        # ANB > 4 (Cl II) but SNA < SNB → impossible
        data = _make_data(analyse_osseuse={
            "SNA": _angle(78), "SNB": _angle(82), "ANB": _angle(5),
        })
        r = self.v.validate(data)
        assert any("Contradiction" in f for f in r.fatals)

    def test_nasolabial_value_is_not_clinically_classified(self):
        data = _make_data(analyse_esthetique={"Angle_Nasolabial": _angle(170)})
        r = self.v.validate(data)
        assert not any("Nasolabial" in message for message in r.fatals + r.warnings)


# ── MM bounds ─────────────────────────────────────────────────────────────────

class TestMmBounds:
    v = cephalo_consistency_validator

    def test_wits_normal_clean(self):
        data = _make_data(analyse_osseuse={"Wits": _mm(0.5)})
        r = self.v.validate(data)
        assert not r.fatals
        assert not r.warnings

    def test_wits_out_of_physio_fatal(self):
        data = _make_data(analyse_osseuse={"Wits": _mm(20.0)})
        r = self.v.validate(data)
        assert any("Wits" in f for f in r.fatals)

    def test_surplomb_out_of_norm_warning(self):
        data = _make_data(analyse_dentaire={"Surplomb": _mm(6.0)})
        r = self.v.validate(data)
        assert r.is_valid
        assert any("Surplomb" in w for w in r.warnings)

    def test_recouvrement_out_of_physio_fatal(self):
        data = _make_data(analyse_dentaire={"Recouvrement": _mm(15.0)})
        r = self.v.validate(data)
        assert any("Recouvrement" in f for f in r.fatals)

    def test_wits_appraisal_real_key_normal_clean(self):
        # Production shape: cephalo_engine.py emits "Wits_Appraisal" under the
        # "wits_mcnamara" section, not bare "Wits" under "analyse_osseuse".
        data = _make_data(wits_mcnamara={"Wits_Appraisal": _mm(0.5)})
        r = self.v.validate(data)
        assert not r.fatals
        assert not r.warnings

    def test_wits_appraisal_real_key_out_of_physio_fatal(self):
        # Regression guard for the name-contract mismatch: "Wits" alone in
        # _MM_METRICS never matched the real "Wits_Appraisal" key, so this
        # physiologically impossible value used to pass through silently.
        data = _make_data(wits_mcnamara={"Wits_Appraisal": _mm(20.0)})
        r = self.v.validate(data)
        assert any("Wits_Appraisal" in f for f in r.fatals)


# ── Unit contradictions ───────────────────────────────────────────────────────

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

    def test_wits_large_value_warning(self):
        # Value > 50 for a mm metric → suspicious
        data = _make_data(analyse_osseuse={
            "Wits": {"valeur": 75.0, "unite": ""}
        })
        r = self.v.validate(data)
        assert any("Wits" in f or "Wits" in w for f in r.fatals for w in r.warnings) or \
               any("Wits" in x for x in r.fatals + r.warnings)

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


# ── Calibration status warning ──────────────────────────────────────────────

class TestCalibrationStatusWarning:
    v = cephalo_consistency_validator

    def test_unverified_calibration_produces_warning(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(82)})
        data["calibration_status"] = "unverified"
        r = self.v.validate(data)
        assert any("Calibration non v" in w for w in r.warnings)
        assert r.is_valid  # WARNING jamais FATAL — les angles restent valides

    def test_verified_calibration_no_warning(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(82)})
        data["calibration_status"] = "verified"
        r = self.v.validate(data)
        assert not any("Calibration non v" in w for w in r.warnings)

    def test_missing_calibration_status_no_warning(self):
        data = _make_data(analyse_osseuse={"SNA": _angle(82)})
        r = self.v.validate(data)
        assert not any("Calibration non v" in w for w in r.warnings)
