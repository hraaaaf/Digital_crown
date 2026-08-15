from __future__ import annotations

from typing import Any

CERTIFICATE_SIGNER_ROLES = frozenset({'ADMIN', 'DENTISTE'})


def certificate_signer_role(user: Any) -> str:
    if user is None:
        return ''
    role = getattr(user, 'role', '')
    value = getattr(role, 'value', role)
    return str(value or '').strip().upper()


def is_authorized_certificate_signer(user: Any) -> bool:
    return certificate_signer_role(user) in CERTIFICATE_SIGNER_ROLES


def resolve_certificate_signer_name(user: Any) -> str:
    if user is None:
        raise ValueError('Praticien signataire introuvable.')
    if not is_authorized_certificate_signer(user):
        raise ValueError('Seul un praticien autorisé peut émettre un certificat.')

    name = str(getattr(user, 'nom_complet', '') or '').strip()
    if not name:
        raise ValueError('Le nom du praticien signataire est requis.')
    return name
