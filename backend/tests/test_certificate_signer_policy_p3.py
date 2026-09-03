from types import SimpleNamespace

import pytest

from backend.services.certificate_signer_policy import (
    is_authorized_certificate_signer,
    resolve_certificate_signer_name,
)


def user(role: str, name: str | None):
    return SimpleNamespace(role=role, nom_complet=name)


def test_dentist_and_admin_roles_can_be_explicit_certificate_signers():
    assert is_authorized_certificate_signer(user('DENTISTE', 'Dr Test')) is True
    assert is_authorized_certificate_signer(user('ADMIN', 'Administrateur')) is True
    assert resolve_certificate_signer_name(user('DENTISTE', '  Dr Test  ')) == 'Dr Test'
    assert resolve_certificate_signer_name(user('ADMIN', '  Administrateur  ')) == 'Administrateur'


def test_non_dentist_roles_cannot_be_implicitly_presented_as_doctor():
    for role, name in [('SECRETAIRE', 'Assistante Test')]:
        candidate = user(role, name)
        assert is_authorized_certificate_signer(candidate) is False
        with pytest.raises(ValueError, match='médecin-dentiste autorisé'):
            resolve_certificate_signer_name(candidate)


def test_certificate_signer_identity_fails_closed_when_missing():
    with pytest.raises(ValueError, match='introuvable'):
        resolve_certificate_signer_name(None)
    with pytest.raises(ValueError, match='nom du praticien'):
        resolve_certificate_signer_name(user('DENTISTE', '   '))
