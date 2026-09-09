from backend.services.prescription_service import PrescriptionService
from backend.services.prescription_service_legacy import PrescriptionService as LegacyPrescriptionService


def test_filters_generic_allergy_warning_but_keeps_specific_penicillin(monkeypatch):
    warnings = [
        {
            "type": "safety",
            "severity": "high",
            "antecedent": "Allergie",
            "drug": "amoxicilline",
            "message": "generic allergy",
        },
        {
            "type": "safety",
            "severity": "high",
            "antecedent": "Pénicilline",
            "drug": "amoxicilline",
            "message": "specific penicillin",
        },
    ]
    monkeypatch.setattr(LegacyPrescriptionService, "check_safety", lambda *args, **kwargs: warnings)

    result = PrescriptionService().check_safety(None, 1, ["amoxicilline"])

    assert result == [warnings[1]]


def test_filters_prophylaxis_omission_but_keeps_ddi(monkeypatch):
    warnings = [
        {
            "type": "omission",
            "severity": "info",
            "drug": "omission-prophylaxie",
            "message": "preventive recall",
        },
        {
            "type": "ddi",
            "severity": "high",
            "drug": "macrolides-simvastatine",
            "message": "ddi",
        },
    ]
    monkeypatch.setattr(LegacyPrescriptionService, "check_safety", lambda *args, **kwargs: warnings)

    result = PrescriptionService().check_safety(None, 1, ["clarithromycine", "simvastatine"])

    assert result == [warnings[1]]
