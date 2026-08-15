from types import SimpleNamespace

import pytest

from backend.services.generators.certificat_gen import (
    CERTIFICATE_REASON_FREE,
    CERTIFICATE_REASON_PRESENCE,
    CERTIFICATE_REASON_WORK_STOP,
    CertificatGenerator,
    _certificate_compression_factors,
    _certificate_reason_kind,
    _safe_filename_component,
)


def test_certificate_filename_component_never_keeps_path_separators_or_control_chars():
    safe = _safe_filename_component('A/B\\C:*?\n Patient')
    assert '/' not in safe
    assert '\\' not in safe
    assert '\n' not in safe
    assert ':' not in safe
    assert '*' not in safe
    assert '?' not in safe
    assert safe


def test_certificate_save_path_keeps_patient_name_inside_output_directory(tmp_path):
    generator = CertificatGenerator(output_dir=str(tmp_path))
    patient = SimpleNamespace(nom='../DUPONT/TEST', prenom='A\\B')
    path = generator._get_save_path(patient, SimpleNamespace())

    assert str(tmp_path) in path
    assert '..' not in path.split('/')[-1]
    assert '\\' not in path.split('/')[-1]


@pytest.mark.parametrize(
    ('reason', 'kind'),
    [
        (CERTIFICATE_REASON_WORK_STOP, 'work_stop'),
        (CERTIFICATE_REASON_PRESENCE, 'presence'),
        (CERTIFICATE_REASON_FREE, 'free'),
    ],
)
def test_generator_accepts_only_canonical_certificate_kinds(reason, kind):
    assert _certificate_reason_kind(reason) == kind


def test_generator_rejects_unknown_reason_instead_of_falling_back_to_work_stop():
    with pytest.raises(ValueError, match='Nature de certificat'):
        _certificate_reason_kind('Présence ou repos selon contexte')


def test_free_medical_certificate_never_shrinks_practitioner_text():
    assert _certificate_compression_factors(True) == (1.0,)


def test_standard_certificate_never_shrinks_below_readable_floor():
    factors = _certificate_compression_factors(False)
    assert min(factors) >= 0.7
    assert factors[0] == 1.0
