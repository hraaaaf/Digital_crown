from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.routers.documents import DOCUMENT_TYPE_PERMISSIONS, require_document_permission


def _user(*, role: str, employer_id, permissions: dict[str, bool]):
    return SimpleNamespace(
        role=role,
        employer_id=employer_id,
        permissions=permissions,
        email="collaborateur@example.test",
    )


def test_document_libre_and_letter_types_require_clinical_permission():
    assert DOCUMENT_TYPE_PERMISSIONS["libre"] == "clinical"
    assert DOCUMENT_TYPE_PERMISSIONS["lettre"] == "clinical"
    assert DOCUMENT_TYPE_PERMISSIONS["lettre_medicale"] == "clinical"
    assert DOCUMENT_TYPE_PERMISSIONS["document_libre"] == "clinical"


def test_secretary_with_patient_access_but_without_clinical_permission_is_refused():
    secretary = _user(
        role="SECRETAIRE",
        employer_id=1,
        permissions={"patients": True, "clinical": False},
    )

    with pytest.raises(HTTPException) as exc_info:
        require_document_permission("libre", secretary)

    assert exc_info.value.status_code == 403
    assert "clinical" in str(exc_info.value.detail)


def test_primary_dentist_is_allowed_by_existing_permission_policy():
    dentist = _user(
        role="DENTISTE",
        employer_id=None,
        permissions={},
    )

    require_document_permission("libre", dentist)


def test_collaborator_with_explicit_clinical_permission_is_allowed():
    delegated = _user(
        role="SECRETAIRE",
        employer_id=1,
        permissions={"patients": True, "clinical": True},
    )

    require_document_permission("lettre", delegated)


def test_unrelated_document_permission_mappings_remain_unchanged():
    assert DOCUMENT_TYPE_PERMISSIONS["ordonnance"] == "prescriptions"
    assert DOCUMENT_TYPE_PERMISSIONS["devis"] == "accounting"
    assert DOCUMENT_TYPE_PERMISSIONS["honoraires"] == "accounting"
    assert DOCUMENT_TYPE_PERMISSIONS["photo_clinique"] == "patients"
    assert DOCUMENT_TYPE_PERMISSIONS["radiographie"] == "patients"
    assert DOCUMENT_TYPE_PERMISSIONS["echeancier"] == "accounting"
