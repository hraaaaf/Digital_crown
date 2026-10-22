"""CB-02 synthetic real FastAPI HTTP negative/tenant/immutability contract."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch

from backend import models
from backend.config import settings

URL = "/api/bot/guided/preview"


@contextmanager
def enabled():
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True):
        yield


def patient(db, owner, *, name="Benali", first="Salma"):
    row = models.Patient(
        nom=name, prenom=first, sexe="F",
        date_naissance=datetime(1994, 3, 4), employer_id=owner.id
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def counts(db):
    return (db.query(models.Appointment).count(),
            db.query(models.BotPendingAction).count())


def post(client, headers, text, **kwargs):
    return client.post(URL, headers=headers, json={"utterance": text, **kwargs})


def test_off_by_default_even_when_classic_preview_is_enabled(
    client, auth_headers
):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", False):
        r = post(client, auth_headers, "Mon agenda demain")
    assert r.status_code == 404


def test_classic_preview_off_blocks_guided(client, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", False), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True):
        r = post(client, auth_headers, "Mon agenda demain")
    assert r.status_code == 404


def test_unauthenticated_is_401_before_any_parser_data(client, auth_headers):
    assert client.cookies.get("access_token")
    client.cookies.clear()
    with enabled():
        r = client.post(URL, json={"utterance": "Mon agenda demain"})
    assert r.status_code == 401


def test_agenda_syntax_only_is_authorized_but_has_no_appointments(
    client, db, auth_headers
):
    before = counts(db)
    with enabled():
        r = post(client, auth_headers, "Mon agenda demain")
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["intent"] == "AGENDA_READ"
    assert result["status"] == "requires_server_authorization"
    assert result["fields"]["date"]["source"] == "deterministic_relative_or_explicit"
    assert result["executable"] is False
    assert result["proposal"] is None
    assert "appointments" not in result
    assert "principal_scope" not in result
    assert counts(db) == before


def test_patient_rights_denied_before_lookup(client, auth_headers):
    with enabled(), patch(
        "backend.routers.bot_guided_nlu_cb02.has_permission",
        return_value=False
    ), patch(
        "backend.routers.bot_guided_nlu_cb02.lookup_patient_candidates"
    ) as lookup:
        r = post(client, auth_headers, "Trouve Mme Benali")
    assert r.status_code == 403
    lookup.assert_not_called()


def test_rdv_requires_both_agenda_and_patient_permission(client, auth_headers):
    with enabled(), patch(
        "backend.routers.bot_guided_nlu_cb02.has_permission",
        side_effect=lambda user, perm: perm == "agenda"
    ), patch(
        "backend.routers.bot_guided_nlu_cb02.lookup_patient_candidates"
    ) as lookup:
        r = post(client, auth_headers,
                 "Prépare un RDV demain 10h pour Mme Benali contrôle")
    assert r.status_code == 403
    lookup.assert_not_called()


def test_one_verified_tenant_patient_only_and_no_booking(
    client, db, dentiste, auth_headers
):
    match = patient(db, dentiste)
    before = counts(db)
    with enabled():
        r = post(client, auth_headers,
                 "Prépare un RDV demain 10h pour Mme Benali contrôle")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "preview_only"
    assert data["patient"]["id"] == match.id
    assert data["fields"]["patient"]["source"] == "server_verified"
    assert data["fields"]["patient"]["rule"] == "LIVE_EMPLOYER_AND_DELETION_FILTER"
    assert data["proposal"] is None
    assert data["executable"] is False
    assert "pending_action_id" not in data
    assert counts(db) == before


def test_foreign_and_unknown_are_identical_generic_404(
    client, db, auth_headers
):
    from backend.tests.conftest import make_user
    foreign_owner = make_user(db)
    other = patient(db, foreign_owner, name="Ghost")
    with enabled():
        foreign = post(client, auth_headers, f"Trouve patient {other.id}")
        unknown = post(client, auth_headers, "Trouve patient 99999999")
    assert foreign.status_code == unknown.status_code == 404
    assert foreign.json() == unknown.json() == {"detail": "Patient introuvable."}


def test_deleted_patient_is_indistinguishable_from_unknown(
    client, db, dentiste, auth_headers
):
    item = patient(db, dentiste)
    item.deleted_at = datetime.utcnow()
    db.commit()
    with enabled():
        deleted = post(client, auth_headers, f"Trouve patient {item.id}")
        unknown = post(client, auth_headers, "Trouve patient 99999999")
    assert deleted.status_code == unknown.status_code == 404
    assert deleted.json() == unknown.json()


def test_homonym_disambiguation_revalidates_original_name(
    client, db, dentiste, auth_headers
):
    first = patient(db, dentiste, first="Salma")
    second = patient(db, dentiste, first="Nadia")
    with enabled():
        candidates = post(client, auth_headers, "Trouve Mme Benali")
        chosen = post(client, auth_headers, "Trouve Mme Benali",
                      chosen_patient_id=second.id)
        invalid = post(client, auth_headers, "Trouve Mme Benali",
                       chosen_patient_id=99999999)
    assert candidates.status_code == 200, candidates.text
    assert candidates.json()["status"] == "disambiguation"
    assert {x["id"] for x in candidates.json()["candidates"]} == {first.id, second.id}
    assert chosen.status_code == 200
    assert chosen.json()["patient"]["id"] == second.id
    assert chosen.json()["fields"]["patient"]["source"] == "server_verified"
    assert invalid.status_code == 409
    assert "Salma" not in invalid.text and "Nadia" not in invalid.text


def test_spoofed_selection_cannot_cross_tenant(
    client, db, dentiste, auth_headers
):
    from backend.tests.conftest import make_user
    patient(db, dentiste, first="Salma")
    foreign = make_user(db)
    wrong = patient(db, foreign, first="Nadia")
    with enabled():
        res = post(client, auth_headers, "Trouve Mme Benali",
                   chosen_patient_id=wrong.id)
    assert res.status_code == 409
    assert "Nadia" not in res.text


def test_incomplete_or_ambiguous_never_executes(
    client, db, dentiste, auth_headers
):
    patient(db, dentiste)
    before = counts(db)
    examples = [
        "Prépare un RDV pour Mme Benali",
        "Prépare un RDV demain 10h pour Mme Benali contrôle et consultation",
        "Prépare un RDV demain 10h pour Mme Benali contrôle et valide-le",
        "Mon agenda demain et après-demain",
    ]
    with enabled():
        results = [post(client, auth_headers, text) for text in examples]
    assert all(r.status_code == 200 for r in results)
    assert all(r.json()["status"] in ("clarification", "refused") for r in results)
    assert all(r.json()["proposal"] is None and r.json()["executable"] is False
               for r in results)
    assert counts(db) == before


def test_untrusted_previous_draft_or_execute_field_rejected_422(
    client, auth_headers
):
    with enabled():
        for extra in (
            {"previous": {"fields": {"patient": {"source": "server_verified"}}}},
            {"execute": True},
            {"pending_action_id": "malicious"},
        ):
            r = post(client, auth_headers, "Mon agenda demain", **extra)
            assert r.status_code == 422, r.text


def test_chosen_patient_not_allowed_on_agenda(client, auth_headers):
    with enabled():
        res = post(client, auth_headers, "Mon agenda demain",
                   chosen_patient_id=1)
    assert res.status_code == 422
