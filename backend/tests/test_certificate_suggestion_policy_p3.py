from datetime import datetime

from backend.services.certificate_suggestion_policy import (
    build_certificate_context_signal,
    certificate_same_day_bounds,
)


def test_same_day_bounds_exclude_tomorrow():
    start, end = certificate_same_day_bounds(datetime(2026, 8, 15, 19, 30))
    assert start == datetime(2026, 8, 15, 0, 0)
    assert end == datetime(2026, 8, 16, 0, 0)


def test_no_same_day_evidence_means_no_suggestion():
    assert build_certificate_context_signal('', has_same_day_visit=False) is None
    assert build_certificate_context_signal('extraction', has_same_day_visit=False) is None


def test_surgery_signal_is_canonical_and_has_no_duration():
    signal = build_certificate_context_signal('Extraction 36', has_same_day_visit=True)
    assert signal is not None
    assert signal['type'] == 'Arrêt de travail'
    assert 'days' not in signal
    assert 'durée' in signal['reason'].lower()
    assert 'praticien' in signal['reason'].lower()


def test_orthodontic_visit_only_signals_presence():
    signal = build_certificate_context_signal('Ajustement appareil ortho', has_same_day_visit=True)
    assert signal is not None
    assert signal['type'] == 'Certificat de Présence'
    assert 'days' not in signal


def test_fitness_or_sport_word_does_not_create_medical_fitness_certificate():
    assert build_certificate_context_signal('Certificat aptitude sport', has_same_day_visit=True) is None
