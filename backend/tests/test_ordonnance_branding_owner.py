from types import SimpleNamespace

from backend.services.document_provenance_context import document_branding_owner_id


def test_ordonnance_branding_uses_employer_for_sub_dentist():
    user = SimpleNamespace(id=91, employer_id=12, get_employer_id=lambda: 12)
    assert document_branding_owner_id(user, 91) == 12


def test_ordonnance_branding_falls_back_to_current_user_without_user_object():
    assert document_branding_owner_id(None, 91) == 91


def test_ordonnance_branding_falls_back_to_explicit_employer_attribute():
    user = SimpleNamespace(id=91, employer_id=12)
    assert document_branding_owner_id(user, 91) == 12
