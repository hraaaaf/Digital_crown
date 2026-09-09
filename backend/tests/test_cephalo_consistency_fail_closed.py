from backend.services.cephalo_consistency_validator import CephaloConsistencyValidator


def metric(value, unit=""):
    return {"valeur": value, "unite": unit}


def test_unsourced_clinical_ranges_do_not_create_warnings_or_fatals():
    data = {
        "analyse_osseuse": {
            "SNA": metric(100.0),
            "SNB": metric(95.0),
            "ANB": metric(5.0),
        },
        "analyse_dentaire": {
            "IMPA": metric(120.0),
            "I_Francfort": metric(140.0),
            "Surplomb": metric(10.0, "mm"),
        },
    }
    result = CephaloConsistencyValidator().validate(data)
    assert result.fatals == []
    assert result.warnings == []


def test_sna_snb_anb_arithmetic_contradiction_remains_fatal():
    data = {
        "analyse_osseuse": {
            "SNA": metric(82.0),
            "SNB": metric(80.0),
            "ANB": metric(8.0),
        }
    }
    result = CephaloConsistencyValidator().validate(data)
    assert not result.is_valid
    assert any("Incohérence interne" in msg for msg in result.fatals)


def test_mm_metric_tagged_as_degrees_remains_fatal():
    data = {
        "analyse_dentaire": {
            "Surplomb": metric(3.0, "°"),
        }
    }
    result = CephaloConsistencyValidator().validate(data)
    assert not result.is_valid
    assert any("Unité contradictoire" in msg for msg in result.fatals)


def test_unverified_calibration_is_warning_not_clinical_classification():
    data = {
        "calibration_status": "unverified",
        "analyse_osseuse": {},
    }
    result = CephaloConsistencyValidator().validate(data)
    assert result.is_valid
    assert len(result.warnings) == 1
    assert "Calibration non vérifiée" in result.warnings[0]
