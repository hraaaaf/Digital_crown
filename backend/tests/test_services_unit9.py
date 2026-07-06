"""Ninth batch — CephaloConsistencyValidator full coverage,
_val helper, ValidationResult dataclass."""


# ── _val helper ───────────────────────────────────────────────────────────────

class TestValHelper:
    def _fn(self, obj, *keys):
        from backend.services.cephalo_consistency_validator import _val
        return _val(obj, *keys)

    def test_flat_dict_returns_value(self):
        assert self._fn({"SNA": {"valeur": 82.0}}, "SNA", "valeur") == 82.0

    def test_nested_value_extraction(self):
        obj = {"osseuse": {"SNA": {"valeur": 82.0}}}
        assert self._fn(obj, "osseuse", "SNA", "valeur") == 82.0

    def test_missing_key_returns_none(self):
        assert self._fn({"SNA": 82.0}, "SNB") is None

    def test_non_dict_intermediate_returns_none(self):
        assert self._fn("not a dict", "key") is None

    def test_none_value_returns_none(self):
        assert self._fn({"SNA": {"valeur": None}}, "SNA", "valeur") is None

    def test_string_number_converted_to_float(self):
        result = self._fn({"v": {"valeur": "80.5"}}, "v", "valeur")
        assert result == 80.5

    def test_nested_dict_extracts_valeur(self):
        # If the final object is itself a dict with "valeur"
        result = self._fn({"k": {"valeur": 42.0}}, "k")
        assert result == 42.0

    def test_empty_dict_returns_none(self):
        assert self._fn({}, "SNA") is None


# ── ValidationResult dataclass ────────────────────────────────────────────────

class TestValidationResult:
    def _make(self):
        from backend.services.cephalo_consistency_validator import ValidationResult
        return ValidationResult()

    def test_default_is_valid(self):
        r = self._make()
        assert r.is_valid is True

    def test_fatal_makes_invalid(self):
        r = self._make()
        r.fatals.append("Fatal error")
        assert r.is_valid is False

    def test_warning_does_not_make_invalid(self):
        r = self._make()
        r.warnings.append("just a warning")
        assert r.is_valid is True

    def test_to_dict_structure(self):
        r = self._make()
        d = r.to_dict()
        assert "valid" in d
        assert "fatals" in d
        assert "warnings" in d

    def test_to_dict_valid_true_when_no_fatals(self):
        r = self._make()
        assert r.to_dict()["valid"] is True

    def test_to_dict_valid_false_with_fatal(self):
        r = self._make()
        r.fatals.append("error")
        assert r.to_dict()["valid"] is False

    def test_to_dict_lists_are_correct(self):
        r = self._make()
        r.fatals.append("F1")
        r.warnings.append("W1")
        d = r.to_dict()
        assert "F1" in d["fatals"]
        assert "W1" in d["warnings"]


# ── CephaloConsistencyValidator.validate ─────────────────────────────────────

class TestCephaloConsistencyValidatorValidate:
    def _v(self):
        from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
        return CephaloConsistencyValidator()

    def _make_angles(self, sna=82.0, snb=80.0, anb=2.0, impa=90.0,
                     inter=125.0, i_franc=100.0, nasolab=100.0):
        return {
            "metrics": {
                "analyse_osseuse": {
                    "SNA": {"valeur": sna},
                    "SNB": {"valeur": snb},
                    "ANB": {"valeur": anb},
                },
                "analyse_dentaire": {
                    "IMPA": {"valeur": impa},
                    "Inter_Incisif": {"valeur": inter},
                    "I_Francfort": {"valeur": i_franc},
                },
                "analyse_esthetique": {
                    "Angle_Nasolabial": {"valeur": nasolab},
                },
            }
        }

    def test_valid_normal_values(self):
        v = self._v()
        result = v.validate(self._make_angles())
        assert result.is_valid

    def test_returns_validation_result(self):
        from backend.services.cephalo_consistency_validator import ValidationResult
        result = self._v().validate(self._make_angles())
        assert isinstance(result, ValidationResult)

    def test_non_dict_input_produces_fatal(self):
        v = self._v()
        result = v.validate("not a dict")
        assert not result.is_valid
        assert len(result.fatals) > 0

    def test_empty_dict_is_valid(self):
        v = self._v()
        result = v.validate({})
        assert result.is_valid

    def test_sna_out_of_hard_bounds_fatal(self):
        v = self._v()
        # SNA hard bounds [60, 105] — 110 is out
        result = v.validate(self._make_angles(sna=110.0, anb=110.0 - 80.0))
        assert not result.is_valid
        assert any("SNA" in f for f in result.fatals)

    def test_snb_out_of_hard_bounds_fatal(self):
        v = self._v()
        # SNB hard bounds [58, 102] — 55 is out
        result = v.validate(self._make_angles(snb=55.0, anb=82.0 - 55.0))
        assert not result.is_valid
        assert any("SNB" in f for f in result.fatals)

    def test_anb_inconsistency_fatal(self):
        v = self._v()
        # SNA=82, SNB=80 → expected ANB=2, but we give ANB=8 (>1.5° off)
        result = v.validate(self._make_angles(sna=82.0, snb=80.0, anb=8.0))
        assert not result.is_valid
        assert any("ANB" in f or "Incohérence" in f for f in result.fatals)

    def test_class_ii_with_sna_less_than_snb_fatal(self):
        v = self._v()
        # ANB > 4 (Class II) but SNA < SNB → contradiction
        result = v.validate(self._make_angles(sna=78.0, snb=80.0, anb=5.0))
        assert not result.is_valid
        assert any("Classe II" in f or "Contradiction" in f for f in result.fatals)

    def test_sna_out_of_soft_bounds_warning(self):
        v = self._v()
        # SNA soft bounds [76, 88] — 90 is outside soft but inside hard
        result = v.validate(self._make_angles(sna=90.0, snb=87.0, anb=3.0))
        assert result.is_valid  # no fatal
        assert any("SNA" in w for w in result.warnings)

    def test_impa_out_of_soft_bounds_warning(self):
        v = self._v()
        # IMPA soft [80, 105] — 110 is outside soft but inside hard [60, 125]
        result = v.validate(self._make_angles(impa=110.0))
        assert result.is_valid
        assert any("IMPA" in w for w in result.warnings)

    def test_normal_values_no_warnings(self):
        v = self._v()
        result = v.validate(self._make_angles(
            sna=82.0, snb=80.0, anb=2.0,
            impa=90.0, inter=125.0, i_franc=100.0, nasolab=100.0
        ))
        assert result.is_valid
        assert len(result.fatals) == 0

    def test_singleton_importable(self):
        from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
        assert cephalo_consistency_validator is not None


# ── _iter_metrics helper ──────────────────────────────────────────────────────

class TestIterMetrics:
    def _fn(self, metrics):
        from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator
        return list(CephaloConsistencyValidator._iter_metrics(metrics))

    def test_empty_dict_yields_nothing(self):
        assert self._fn({}) == []

    def test_single_metric_yielded(self):
        metrics = {"section": {"SNA": {"valeur": 82.0, "unite": "°"}}}
        results = self._fn(metrics)
        assert len(results) == 1
        name, val, unite = results[0]
        assert name == "SNA"
        assert val == 82.0
        assert unite == "°"

    def test_invalid_value_skipped(self):
        metrics = {"section": {"SNA": {"valeur": "invalid", "unite": "°"}}}
        results = self._fn(metrics)
        assert len(results) == 0

    def test_none_value_skipped(self):
        metrics = {"section": {"SNA": {"valeur": None, "unite": "°"}}}
        results = self._fn(metrics)
        assert len(results) == 0

    def test_multiple_sections(self):
        metrics = {
            "sec1": {"SNA": {"valeur": 82.0, "unite": "°"}},
            "sec2": {"SNB": {"valeur": 80.0, "unite": "°"}},
        }
        results = self._fn(metrics)
        names = [r[0] for r in results]
        assert "SNA" in names
        assert "SNB" in names

    def test_non_dict_section_skipped(self):
        metrics = {"section": "not a dict"}
        results = self._fn(metrics)
        assert len(results) == 0


# ── mm metric unit contradiction check ───────────────────────────────────────

class TestCheckUnitContradictions:
    def _v(self):
        from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator, ValidationResult
        return CephaloConsistencyValidator(), ValidationResult()

    def test_mm_metric_with_degree_unit_is_fatal(self):
        v, result = self._v()
        metrics = {"section": {"Wits": {"valeur": 2.0, "unite": "°"}}}
        v._check_unit_contradictions(metrics, result)
        assert len(result.fatals) > 0
        assert any("Wits" in f for f in result.fatals)

    def test_mm_metric_with_mm_unit_is_ok(self):
        v, result = self._v()
        metrics = {"section": {"Wits": {"valeur": 2.0, "unite": "mm"}}}
        v._check_unit_contradictions(metrics, result)
        assert len(result.fatals) == 0

    def test_angle_metric_not_affected(self):
        v, result = self._v()
        metrics = {"section": {"SNA": {"valeur": 82.0, "unite": "°"}}}
        v._check_unit_contradictions(metrics, result)
        assert len(result.fatals) == 0

    def test_very_large_mm_value_triggers_warning(self):
        v, result = self._v()
        metrics = {"section": {"Surplomb": {"valeur": 200.0, "unite": "mm"}}}
        v._check_unit_contradictions(metrics, result)
        assert len(result.warnings) > 0
