import pytest
from pydantic import ValidationError

from backend.schemas.auth import (
    UserSignup,
    TrialActivationRequest,
    TeamMemberCreate,
    TeamMemberUpdate,
    PASSWORD_MIN_LENGTH,
)


def test_password_minimum_is_eight():
    assert PASSWORD_MIN_LENGTH == 8


@pytest.mark.parametrize("schema,payload", [
    (UserSignup, {
        "email": "signup@cabinet.test", "password": "1234567", "nom_complet": "Dr Test",
        "accept_terms": True, "accept_privacy": True,
    }),
    (TrialActivationRequest, {
        "code": "ABCDEF", "email": "trial@cabinet.test", "password": "1234567",
        "nom_complet": "Dr Test", "accept_terms": True, "accept_privacy": True,
    }),
    (TeamMemberCreate, {
        "email": "team@cabinet.test", "password": "1234567", "nom_complet": "Assistant Test",
    }),
    (TeamMemberUpdate, {"new_password": "1234567"}),
])
def test_seven_character_password_is_rejected(schema, payload):
    with pytest.raises(ValidationError):
        schema(**payload)


@pytest.mark.parametrize("schema,payload", [
    (UserSignup, {
        "email": "signup-ok@cabinet.test", "password": "12345678", "nom_complet": "Dr Test",
        "accept_terms": True, "accept_privacy": True,
    }),
    (TrialActivationRequest, {
        "code": "ABCDEF", "email": "trial-ok@cabinet.test", "password": "12345678",
        "nom_complet": "Dr Test", "accept_terms": True, "accept_privacy": True,
    }),
    (TeamMemberCreate, {
        "email": "team-ok@cabinet.test", "password": "12345678", "nom_complet": "Assistant Test",
    }),
    (TeamMemberUpdate, {"new_password": "12345678"}),
])
def test_eight_character_password_is_accepted(schema, payload):
    schema(**payload)
