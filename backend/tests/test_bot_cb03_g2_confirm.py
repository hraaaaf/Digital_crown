"""CB-03 G2 synthetic HTTP/SQL contract for explicit atomic confirmation."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from backend import models
from backend.config import settings
from backend.services.bot.action_dispatcher import BotResponse

CONFIRM = "/api/bot/guided/confirm"
ACTIONS = "/api/bot/guided/actions/"
STATUS_PREPARE = "/api/bot/guided/prepare-status"
BOOK_PREPARE = "/api/bot/guided/prepare-appointment"


@contextmanager
def enabled():
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_PREPARATION_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_CONFIRMATION_ENABLED", True):
        yield


def patient(db, user, name="Benali", first="Salma"):
    p = models.Patient(
        nom=name, prenom=first, sexe="F",
        date_naissance=datetime(1994, 3, 4), employer_id=user.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def appointment(db, user, p, status=models.AppointmentStatus.PREVU):
    a = models.Appointment(
        patient_id=p.id, employer_id=user.get_employer_id(),
        datetime_start=datetime.now() + timedelta(days=20),
        duration_minutes=30, motif="Synthetic", status=status,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def prepare_status(client, headers, a, new="salle d'attente"):
    return client.post(STATUS_PREPARE, headers=headers, json={
        "selected_appointment_id": a.id,
        "utterance": f"Prépare le statut du RDV en {new}",
    })


def future_monday():
    day = (datetime.now(ZoneInfo(settings.CROWN_BOT_CABINET_TIMEZONE))
           + timedelta(days=15)).date()
    while day.weekday() != 0:
        day += timedelta(days=1)
    return day.isoformat()


def prepare_booking(client, headers):
    return client.post(BOOK_PREPARE, headers=headers, json={
        "utterance": f"Prépare un RDV le {future_monday()} à 10h pour Mme Benali contrôle",
        "duration_minutes": 30,
    })


def confirm(client, headers, action_id, **extras):
    return client.post(CONFIRM, headers=headers, json={
        "preparation_id": action_id, "confirm": True, **extras,
    })


def count_confirm_audits(db):
    return db.query(models.AuditLog).filter_by(action="CB03_ACTION_CONFIRMED").count()


def test_flag_off_blocks_confirm_and_reconcile(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    assert prep.status_code == 200, prep.text
    action_id = prep.json()["preparation_id"]
    with enabled(), patch.object(settings, "CROWN_BOT_CB03_CONFIRMATION_ENABLED", False):
        out = confirm(client, auth_headers, action_id)
        read = client.get(ACTIONS + action_id, headers=auth_headers)
    assert out.status_code == read.status_code == 404
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU


def test_confirm_requires_auth_and_strict_confirmation(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
        assert prep.status_code == 200
        action_id = prep.json()["preparation_id"]
        responses = [
            confirm(client, auth_headers, action_id, confirm=False),
            confirm(client, auth_headers, action_id, confirm="true"),
            confirm(client, auth_headers, action_id, status="TERMINE"),
            client.post(CONFIRM, headers=auth_headers, json={"preparation_id": action_id}),
            confirm(client, auth_headers, "not-a-uuid"),
        ]
    assert [r.status_code for r in responses] == [422] * 5
    assert count_confirm_audits(db) == 0
    client.cookies.clear()
    with enabled():
        response = client.post(CONFIRM, json={
            "preparation_id": action_id, "confirm": True,
        })
    assert response.status_code == 401


def test_status_confirm_atomic_success_replay_reconciliation(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    expected_revision = a.clinical_revision
    with enabled():
        prepared = prepare_status(client, auth_headers, a)
        assert prepared.status_code == 200, prepared.text
        action_id = prepared.json()["preparation_id"]
        before = client.get(ACTIONS + action_id, headers=auth_headers)
        assert before.status_code == 200
        assert before.json()["status"] == "prepared"
        assert before.json()["result"] is None
        assert before.json()["safe_to_retry_automatically"] is False
        response = confirm(client, auth_headers, action_id)
        replay = confirm(client, auth_headers, action_id)
        after = client.get(ACTIONS + action_id, headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "executed"
    assert response.json()["result"] == {"appointment_id": a.id, "status": "EN_SALLE_ATTENTE"}
    assert replay.status_code == 409
    assert after.status_code == 200
    assert after.json()["status"] == "executed"
    assert after.json()["result"] == response.json()["result"]
    assert after.json()["safe_to_retry_automatically"] is False
    db.expire_all()
    a = db.query(models.Appointment).filter_by(id=a.id).one()
    assert a.status == models.AppointmentStatus.EN_SALLE_ATTENTE
    assert a.clinical_revision == expected_revision + 1
    action = db.query(models.BotPendingAction).filter_by(id=action_id).one()
    assert action.status == "executed"
    assert action.params_json["_cb03_receipt"]["appointment_id"] == a.id
    assert count_confirm_audits(db) == 1
    assert db.query(models.AuditLog).filter_by(
        action="UPDATE", resource_type="Appointment", resource_id=str(a.id)
    ).count() == 1


def test_book_confirm_canonical_and_no_duplicate(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    with enabled():
        prep = prepare_booking(client, auth_headers)
        assert prep.status_code == 200, prep.text
        action_id = prep.json()["preparation_id"]
        before = db.query(models.Appointment).count()
        result = confirm(client, auth_headers, action_id)
        replay = confirm(client, auth_headers, action_id)
        reconciled = client.get(ACTIONS + action_id, headers=auth_headers)
    assert result.status_code == 200, result.text
    assert result.json()["result"]["status"] == "CREATED"
    assert replay.status_code == 409
    assert reconciled.status_code == 200
    assert reconciled.json()["result"] == result.json()["result"]
    assert db.query(models.Appointment).count() == before + 1
    booked = db.query(models.Appointment).filter_by(
        id=result.json()["result"]["appointment_id"]
    ).one()
    assert booked.patient_id == p.id and booked.employer_id == dentiste.id
    assert booked.praticien_id == dentiste.id
    assert count_confirm_audits(db) == 1


def test_status_stale_revision_aba_is_rejected_with_no_new_mutation(
    client, db, dentiste, auth_headers,
):
    from sqlalchemy import text
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action_id = prep.json()["preparation_id"]
    db.execute(text("UPDATE appointments SET status='ANNULE' WHERE id=:id"), {"id": a.id})
    db.execute(text("UPDATE appointments SET status='PREVU' WHERE id=:id"), {"id": a.id})
    db.commit()
    db.refresh(a)
    rev = a.clinical_revision
    with enabled():
        attempt = confirm(client, auth_headers, action_id)
    assert attempt.status_code == 409
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU
    assert a.clinical_revision == rev
    action = db.query(models.BotPendingAction).filter_by(id=action_id).one()
    assert action.status == "prepared"
    assert count_confirm_audits(db) == 0


def test_permission_change_after_prepare_blocks_confirmation(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action_id = prep.json()["preparation_id"]
    with enabled(), patch(
        "backend.routers.bot_cb03_confirm_g2.has_permission",
        side_effect=lambda _user, perm: perm == "agenda",
    ):
        denied = confirm(client, auth_headers, action_id)
        hidden = client.get(ACTIONS + action_id, headers=auth_headers)
    assert denied.status_code == hidden.status_code == 403
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU
    assert count_confirm_audits(db) == 0


def test_foreign_owner_cannot_confirm_or_read_action(
    client, db, dentiste, auth_headers,
):
    from backend.tests.conftest import make_user
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action_id = prep.json()["preparation_id"]
    foreign_user = make_user(db)
    login = client.post("/api/auth/login", data={
        "username": foreign_user.email, "password": "TestPass123!",
    })
    assert login.status_code == 200, login.text
    foreign_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    with enabled():
        denied = confirm(client, foreign_headers, action_id)
        hidden = client.get(ACTIONS + action_id, headers=foreign_headers)
    assert denied.status_code == hidden.status_code == 404
    assert db.query(models.Appointment).filter_by(id=a.id).one().status == (
        models.AppointmentStatus.PREVU
    )
    assert count_confirm_audits(db) == 0


def test_expiration_prevents_confirmation_and_get_reports_expired(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    action.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db.commit()
    with enabled():
        expired = confirm(client, auth_headers, action.id)
        read = client.get(ACTIONS + action.id, headers=auth_headers)
    assert expired.status_code == 410
    assert read.status_code == 200
    assert read.json()["status"] == "expired"
    assert read.json()["safe_to_retry_automatically"] is False
    assert action.status == "prepared"
    assert count_confirm_audits(db) == 0


def test_unexpected_dispatcher_result_rolls_back_claim_and_business_write(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action_id = prep.json()["preparation_id"]
    initial_revision = a.clinical_revision

    def partial_write(_action, session, _user, *, transactional=False):
        assert transactional is True
        session.query(models.Appointment).filter_by(id=a.id).update(
            {"status": models.AppointmentStatus.EN_SALLE_ATTENTE},
            synchronize_session=False,
        )
        session.flush()
        return BotResponse("error", action_type="error")

    with enabled(), patch(
        "backend.routers.bot_cb03_confirm_g2.dispatcher.execute",
        side_effect=partial_write,
    ):
        denied = confirm(client, auth_headers, action_id)
    assert denied.status_code == 409
    db.expire_all()
    db_a = db.query(models.Appointment).filter_by(id=a.id).one()
    assert db_a.status == models.AppointmentStatus.PREVU
    assert db_a.clinical_revision == initial_revision
    action = db.query(models.BotPendingAction).filter_by(id=action_id).one()
    assert action.status == "prepared"
    assert count_confirm_audits(db) == 0


def test_prepared_payload_tampering_fails_closed(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    action.params_json = {**action.params_json, "expected_revision": None}
    db.commit()
    with enabled():
        denied = confirm(client, auth_headers, action.id)
    assert denied.status_code == 409
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU
    assert count_confirm_audits(db) == 0


def test_unsupported_legacy_pending_action_in_same_session_cannot_be_consumed(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    action.status = "pending"  # simulate pre-upgrade untrusted pending state
    db.commit()
    with enabled():
        denied = confirm(client, auth_headers, action.id)
    assert denied.status_code == 409
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU


def test_executing_never_claimed_again_and_get_requires_manual_reconciliation(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    action.status = "executing"  # simulate legacy durable uncertain state
    db.commit()
    with enabled():
        denied = confirm(client, auth_headers, action.id)
        status = client.get(ACTIONS + action.id, headers=auth_headers)
    assert denied.status_code == 409
    assert status.status_code == 200
    assert status.json()["status"] == "executing"
    assert status.json()["manual_reconciliation_required"] is True
    assert status.json()["safe_to_retry_automatically"] is False


def test_booking_conflict_added_after_prepare_rejected_without_duplicate(
    client, db, dentiste, auth_headers,
):
    patient(db, dentiste)
    with enabled():
        prep = prepare_booking(client, auth_headers)
    assert prep.status_code == 200, prep.text
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    start = datetime.fromisoformat(action.params_json["datetime_start"])
    blocker = models.Appointment(
        patient_id=action.params_json["patient_id"],
        employer_id=dentiste.id,
        praticien_id=dentiste.id,
        datetime_start=start,
        duration_minutes=30,
        status=models.AppointmentStatus.PREVU,
        motif="Synthetic conflict",
    )
    db.add(blocker)
    db.commit()
    with enabled():
        rejected = confirm(client, auth_headers, action.id)
    assert rejected.status_code == 409, rejected.text
    assert db.query(models.Appointment).count() == 1
    db.refresh(action)
    assert action.status == "prepared"
    assert count_confirm_audits(db) == 0


def test_cancelled_and_unknown_outcome_cannot_be_replayed(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    action.status = "cancelled"
    db.commit()
    with enabled():
        denied = confirm(client, auth_headers, action.id)
        read = client.get(ACTIONS + action.id, headers=auth_headers)
    assert denied.status_code == 409
    assert read.status_code == 200
    assert read.json()["status"] == "cancelled"
    assert count_confirm_audits(db) == 0


def test_foreign_patient_reassigned_after_preparation_fails_closed(
    client, db, dentiste, auth_headers,
):
    p = patient(db, dentiste)
    other = patient(db, dentiste, name="Another", first="Other")
    a = appointment(db, dentiste, p)
    with enabled():
        prep = prepare_status(client, auth_headers, a)
    a.patient_id = other.id
    db.commit()
    with enabled():
        rejected = confirm(client, auth_headers, prep.json()["preparation_id"])
    assert rejected.status_code == 409
    db.refresh(a)
    assert a.patient_id == other.id
    assert a.status == models.AppointmentStatus.PREVU
    assert count_confirm_audits(db) == 0


def test_schema_introspection_preserves_in_flight_prepared_claim(
    client, db, dentiste, auth_headers,
):
    """SQLite StaticPool schema inspection must reuse the transaction connection."""
    from backend.services.bot.atomic_action_claim import claim_prepared_action
    from backend.services.agenda_availability import validate_appointment_availability

    patient(db, dentiste)
    with enabled():
        prep = prepare_booking(client, auth_headers)
    assert prep.status_code == 200, prep.text
    action = db.query(models.BotPendingAction).filter_by(
        id=prep.json()["preparation_id"]
    ).one()
    assert claim_prepared_action(
        db, models.BotPendingAction, action.id, dentiste.id,
        dentiste.id, datetime.utcnow(),
    )
    assert db.query(models.BotPendingAction).filter_by(
        id=action.id, status="executing"
    ).count() == 1
    validate_appointment_availability(
        db, dentiste.id,
        datetime.fromisoformat(action.params_json["datetime_start"]),
        action.params_json["duration_minutes"],
        models.SchedulingType.EXACT_TIME,
        practitioner_id=dentiste.id,
    )
    assert db.query(models.BotPendingAction).filter_by(
        id=action.id, status="executing"
    ).count() == 1, "Schema inspector rolled back the in-flight confirmation CAS"
    db.rollback()
    assert db.query(models.BotPendingAction).filter_by(
        id=action.id, status="prepared"
    ).count() == 1
