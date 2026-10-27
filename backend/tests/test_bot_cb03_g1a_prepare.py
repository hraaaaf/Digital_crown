"""CB-03 G1-A synthetic-only HTTP non-execution and authorization tests."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from backend import models
from backend.config import settings

URL = "/api/bot/guided/prepare-appointment"


@contextmanager
def enabled():
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_PREPARATION_ENABLED", True):
        yield


def slot():
    day = (datetime.now(ZoneInfo(settings.CROWN_BOT_CABINET_TIMEZONE))
           + timedelta(days=15)).date()
    while day.weekday() != 0:
        day += timedelta(days=1)
    return day.isoformat()


def patient(db, owner, *, first="Salma", last="Benali"):
    row = models.Patient(nom=last, prenom=first, sexe="F",
                         date_naissance=datetime(1994, 3, 4), employer_id=owner.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def payload(**extra):
    data = {
        "utterance": f"Prépare un RDV le {slot()} à 10h pour Mme Benali contrôle",
        "duration_minutes": 30,
    }
    data.update(extra)
    return data


def post(client, auth_headers, **extra):
    return client.post(URL, headers=auth_headers, json=payload(**extra))


def test_flag_off_is_404_with_cb02_enabled(client, db, auth_headers):
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_PREPARATION_ENABLED", False):
        r = post(client, auth_headers)
    assert r.status_code == 404
    assert db.query(models.BotPendingAction).count() == 0


def test_unauthenticated_is_401(client, db, auth_headers):
    client.cookies.clear()
    with enabled():
        r = client.post(URL, json=payload())
    assert r.status_code == 401
    assert db.query(models.BotPendingAction).count() == 0


def test_prepare_is_non_executable_and_never_books(
    client, db, dentiste, auth_headers
):
    item = patient(db, dentiste)
    with enabled():
        r = post(client, auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "prepared" and data["executable"] is False
    assert "pending_action_id" not in data
    assert data["summary"]["patient"]["id"] == item.id
    assert data["summary"]["praticien_id"] == dentiste.id
    assert db.query(models.Appointment).count() == 0
    action = db.query(models.BotPendingAction).filter_by(id=data["preparation_id"]).one()
    assert action.status == "prepared" and action.action_type == "CREATE_APPOINTMENT"
    assert action.user_id == dentiste.id and action.employer_id == dentiste.id
    assert action.params_json["patient_id"] == item.id
    assert action.params_json["datetime_start"].endswith("T10:00:00")
    assert timedelta(minutes=28) < action.expires_at - datetime.utcnow() <= timedelta(minutes=30)
    with enabled():
        forbidden = client.post("/api/bot/execute", headers=auth_headers,
                                json={"pending_action_id": action.id})
    assert forbidden.status_code == 409, forbidden.text
    assert db.query(models.Appointment).count() == 0
    db.refresh(action)
    assert action.status == "prepared"


def test_permission_denied_before_patient_lookup(client, auth_headers):
    with enabled(), patch(
        "backend.routers.bot_guided_nlu_cb02.has_permission",
        side_effect=lambda _user, permission: permission == "agenda",
    ), patch(
        "backend.routers.bot_guided_nlu_cb02.lookup_patient_candidates"
    ) as lookup:
        r = post(client, auth_headers)
    assert r.status_code == 403
    lookup.assert_not_called()


def test_foreign_archived_unknown_patient_identical_404(
    client, db, dentiste, auth_headers
):
    from backend.tests.conftest import make_user
    foreign_owner = make_user(db)
    foreign = patient(db, foreign_owner, first="Foreign", last="Ghost")
    archived = patient(db, dentiste, first="Archived", last="Ghost")
    archived.deleted_at = datetime.utcnow()
    db.commit()
    base = payload()["utterance"]
    with enabled():
        r1 = post(client, auth_headers, utterance=base.replace("Mme Benali", f"patient {foreign.id}"))
        r2 = post(client, auth_headers, utterance=base.replace("Mme Benali", f"patient {archived.id}"))
        r3 = post(client, auth_headers, utterance=base.replace("Mme Benali", "patient 99999999"))
    assert r1.status_code == r2.status_code == r3.status_code == 404
    assert r1.json() == r2.json() == r3.json()
    assert db.query(models.BotPendingAction).count() == 0


def test_homonyms_are_not_selected_implicitly(client, db, dentiste, auth_headers):
    a = patient(db, dentiste)
    b = patient(db, dentiste, first="Nadia")
    with enabled():
        ambiguous = post(client, auth_headers)
        wrong = post(client, auth_headers, chosen_patient_id=99999999)
        chosen = post(client, auth_headers, chosen_patient_id=b.id)
    assert ambiguous.status_code == 200
    assert ambiguous.json()["status"] == "disambiguation"
    assert ambiguous.json()["preparation_id"] is None
    assert {p["id"] for p in ambiguous.json()["candidates"]} == {a.id, b.id}
    assert wrong.status_code == 409
    assert chosen.status_code == 200, chosen.text
    assert chosen.json()["summary"]["patient"]["id"] == b.id
    assert db.query(models.Appointment).count() == 0
    assert db.query(models.BotPendingAction).count() == 1


def test_incomplete_or_non_rdv_never_prepared(client, db, dentiste, auth_headers):
    patient(db, dentiste)
    with enabled():
        missing = post(client, auth_headers,
                       utterance="Prépare un RDV demain pour Mme Benali contrôle")
        other = post(client, auth_headers, utterance="Mon agenda demain")
    assert missing.status_code == 200
    assert missing.json()["status"] == "clarification"
    assert missing.json()["preparation_id"] is None
    assert other.status_code == 422
    assert db.query(models.BotPendingAction).count() == 0


def test_extra_fields_and_invalid_ranges_refused(client, db, auth_headers):
    invalid = [
        {"pending_action_id": "forged"}, {"params_json": {"patient_id": 9}},
        {"duration_minutes": 0}, {"duration_minutes": 481},
        {"duration_minutes": True}, {"praticien_id": -1},
        {"chosen_patient_id": "1"}, {"execute": True},
    ]
    with enabled():
        results = [post(client, auth_headers, **case) for case in invalid]
    assert all(r.status_code == 422 for r in results)
    assert db.query(models.BotPendingAction).count() == 0


def test_foreign_practitioner_refused(client, db, dentiste, auth_headers):
    from backend.tests.conftest import make_user
    patient(db, dentiste)
    other = make_user(db)
    with enabled():
        r = post(client, auth_headers, praticien_id=other.id)
    assert r.status_code == 403
    assert db.query(models.BotPendingAction).count() == 0


def test_canonical_availability_and_overlap_reject(client, db, dentiste, auth_headers):
    patient(db, dentiste)
    with enabled(), patch(
        "backend.routers.bot_cb03_safe_actions.validate_appointment_availability",
        return_value="Cabinet ferme.",
    ):
        closed = post(client, auth_headers)
    with enabled(), patch(
        "backend.routers.bot_cb03_safe_actions._find_conflicts",
        return_value=[object()],
    ):
        overlap = post(client, auth_headers)
    assert closed.status_code == 422 and overlap.status_code == 409
    assert db.query(models.BotPendingAction).count() == 0


def test_resource_conflict_is_redacted(client, db, dentiste, auth_headers):
    patient(db, dentiste)
    with enabled(), patch(
        "backend.routers.bot_cb03_safe_actions.validate_assignable_resource",
        return_value=None,
    ), patch(
        "backend.routers.bot_cb03_safe_actions.assert_resource_available",
        side_effect=HTTPException(409, detail={"appointment_id": 999}),
    ):
        r = post(client, auth_headers, resource_id=1)
    assert r.status_code == 409
    assert r.json() == {"detail": "Ressource indisponible."}
    assert db.query(models.BotPendingAction).count() == 0
