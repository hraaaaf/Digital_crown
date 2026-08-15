from datetime import date
import inspect

from backend.services.generators.certificat_gen import (
    CertificatGenerator,
    _build_presence_certificate_text,
    _certificate_closing_text,
)


def test_presence_certificate_only_asserts_observed_presence():
    text = _build_presence_certificate_text(
        "Dentiste Test",
        "Monsieur",
        "PATIENT Test",
        date(2026, 8, 15),
    )

    lowered = text.lower()
    assert "constaté la présence" in lowered
    assert "soins" not in lowered
    assert "orthodont" not in lowered
    assert "bucco" not in lowered


def test_certificate_closing_does_not_invent_hand_delivery_or_patient_request():
    lowered = _certificate_closing_text().lower()
    assert "main propre" not in lowered
    assert "à sa demande" not in lowered


def test_work_stop_generation_no_longer_infers_school_exclusion_from_age():
    source = inspect.getsource(CertificatGenerator.generate).lower()
    assert "éviction scolaire" not in source
    assert 'eviction_term = "un arrêt de travail"' in source
