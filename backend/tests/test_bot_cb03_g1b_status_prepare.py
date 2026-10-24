"""CB-03 G1-B synthetic FastAPI contract: prepare status, never mutate it."""
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest.mock import patch

from sqlalchemy import text

from backend import models
from backend.config import settings
from backend.services.bot.guided_status_cb03 import (
    parse_status_preparation,
    transition_allowed,
)

URL = "/api/bot/guided/prepare-status"


@contextmanager
def enabled():
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED", True):
        yield


def patient(db, owner, *, first="Synthetic", last="Patient"):
    obj = models.Patient(
        nom=last, prenom=first, sexe="F",
        date_naissance=datetime(1990, 1, 1), employer_id=owner.id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def appointment(db, owner, patient_row, *, status=models.AppointmentStatus.PREVU, archived=False):
    obj = models.Appointment(
        patient_id=patient_row.id,
        employer_id=owner.id,
        datetime_start=datetime.now() + timedelta(days=9),
        duration_minutes=30,
        motif="Synthetic",
        status=status,
        deleted_at=datetime.utcnow() if archived else None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def post(client, auth_headers, appointment_id, **extra):
    payload = {
        "selected_appointment_id": appointment_id,
        "utterance": "Prépare le changement de statut du RDV en salle d'attente",
    }
    payload.update(extra)
    return client.post(URL, headers=auth_headers, json=payload)


def count(db):
    return db.query(models.BotPendingAction).count()


def test_flag_off_blocks_and_no_action(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED", False):
        response = post(client, auth_headers, a.id)
    assert response.status_code == 404
    assert count(db) == 0


def test_independent_cb02_gate_required(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with patch.object(settings, "CROWN_BOT_DETERMINISTIC_WORKFLOWS_ENABLED", True), \
         patch.object(settings, "CROWN_BOT_GUIDED_NLU_ENABLED", False), \
         patch.object(settings, "CROWN_BOT_CB03_STATUS_PREPARATION_ENABLED", True):
        response = post(client, auth_headers, a.id)
    assert response.status_code == 404
    assert count(db) == 0


def test_unauthenticated_is_401(client, db, auth_headers):
    client.cookies.clear()
    with enabled():
        response = client.post(URL, json={
            "selected_appointment_id": 1,
            "utterance": "Prépare le statut du RDV en fauteuil",
        })
    assert response.status_code == 401
    assert count(db) == 0


def test_prepare_creates_only_non_executable_action(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    original_revision = a.clinical_revision
    with enabled():
        response = post(client, auth_headers, a.id)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "prepared"
    assert result["executable"] is False
    assert "pending_action_id" not in result
    assert result["summary"]["appointment_id"] == a.id
    assert result["summary"]["patient"]["id"] == p.id
    assert result["summary"]["expected_status"] == "PREVU"
    assert result["summary"]["expected_revision"] == original_revision
    assert result["summary"]["new_status"] == "EN_SALLE_ATTENTE"
    prepared = db.query(models.BotPendingAction).filter_by(
        id=result["preparation_id"]
    ).one()
    assert prepared.action_type == "CHANGE_STATUS"
    assert prepared.status == "prepared"
    assert prepared.user_id == dentiste.id
    assert prepared.employer_id == dentiste.id
    assert prepared.params_json["appointment_id"] == a.id
    assert prepared.params_json["patient_id"] == p.id
    assert prepared.params_json["expected_status"] == "PREVU"
    assert prepared.params_json["expected_revision"] == original_revision
    assert prepared.params_json["status"] == "EN_SALLE_ATTENTE"
    assert timedelta(minutes=28) < prepared.expires_at - datetime.utcnow() <= timedelta(minutes=30)
    assert db.query(models.AuditLog).filter_by(
        action="CB03_STATUS_PREPARED", resource_id=prepared.id
    ).count() == 1
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU
    assert a.clinical_revision == original_revision
    with enabled():
        rejected = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": prepared.id},
        )
    assert rejected.status_code == 409, rejected.text
    db.refresh(a)
    db.refresh(prepared)
    assert a.status == models.AppointmentStatus.PREVU
    assert a.clinical_revision == original_revision
    assert prepared.status == "prepared"


def test_permission_gate_before_patient_and_appointment_data(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    with enabled(), patch(
        "backend.routers.bot_cb03_status_prepare.has_permission",
        side_effect=lambda _user, permission: permission == "agenda",
    ), patch(
        "backend.routers.bot_cb03_status_prepare.parse_status_preparation"
    ) as parser:
        denied = post(client, auth_headers, a.id)
    assert denied.status_code == 403
    parser.assert_not_called()
    assert count(db) == 0


def test_missing_foreign_archived_appointment_same_404(client, db, dentiste, auth_headers):
    from backend.tests.conftest import make_user
    p = patient(db, dentiste)
    archived = appointment(db, dentiste, p, archived=True)
    other = make_user(db)
    foreign_p = patient(db, other)
    foreign = appointment(db, other, foreign_p)
    with enabled():
        responses = [
            post(client, auth_headers, foreign.id),
            post(client, auth_headers, archived.id),
            post(client, auth_headers, 99999999),
        ]
    assert all(r.status_code == 404 for r in responses)
    assert all(r.json() == {"detail": "Rendez-vous introuvable."} for r in responses)
    assert count(db) == 0


def test_deleted_patient_makes_appointment_ineligible(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    p.deleted_at = datetime.utcnow()
    db.commit()
    with enabled():
        response = post(client, auth_headers, a.id)
    assert response.status_code == 404
    assert response.json() == {"detail": "Rendez-vous introuvable."}
    assert count(db) == 0


def test_transition_whitelist_rejects_invalid_and_terminal_states(
    client, db, dentiste, auth_headers
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p, status=models.AppointmentStatus.PREVU)
    with enabled():
        skips = post(client, auth_headers, a.id,
                     utterance="Prépare le statut du RDV en fauteuil")
        same = post(client, auth_headers, a.id,
                    utterance="Prépare le statut du RDV en prévu")
        allowed_cancel = post(client, auth_headers, a.id,
                              utterance="Prépare le statut du RDV en annulé")
    assert skips.status_code == 409
    assert same.status_code == 422
    assert allowed_cancel.status_code == 200
    assert allowed_cancel.json()["summary"]["new_status"] == "ANNULE"

    a.status = models.AppointmentStatus.ANNULE
    db.commit()
    with enabled():
        reactivate = post(client, auth_headers, a.id,
                          utterance="Prépare le statut du RDV en fauteuil")
    assert reactivate.status_code == 409
    assert count(db) == 1


def test_explicit_whitelist_allows_stepwise_dental_flow(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p, status=models.AppointmentStatus.EN_SALLE_ATTENTE)
    with enabled():
        ok = post(client, auth_headers, a.id,
                  utterance="Prépare le statut du RDV en fauteuil")
        illegal = post(client, auth_headers, a.id,
                       utterance="Prépare le statut du RDV en terminé")
    assert ok.status_code == 200
    assert ok.json()["summary"]["expected_status"] == "EN_SALLE_ATTENTE"
    assert illegal.status_code == 409
    a.status = models.AppointmentStatus.EN_FAUTEUIL
    db.commit()
    with enabled():
        finish = post(client, auth_headers, a.id,
                      utterance="Prépare le statut du RDV en terminé")
    assert finish.status_code == 200
    assert finish.json()["summary"]["new_status"] == "TERMINE"
    db.refresh(a)
    assert a.status == models.AppointmentStatus.EN_FAUTEUIL


def test_client_cannot_forge_snapshot_or_execution(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    cases = (
        {"patient_id": p.id}, {"expected_revision": 0},
        {"expected_status": "EN_FAUTEUIL"}, {"status": "ANNULE"},
        {"action_type": "CHANGE_STATUS"}, {"params_json": {"appointment_id": a.id}},
        {"execute": True}, {"pending_action_id": "forged"},
        {"selected_appointment_id": True}, {"selected_appointment_id": "1"},
        {"selected_appointment_id": -1},
    )
    with enabled():
        results = [post(client, auth_headers, a.id, **case) for case in cases]
    assert all(result.status_code == 422 for result in results)
    assert count(db) == 0


def test_missing_explicit_appointment_selection_is_refused(client, db, auth_headers):
    with enabled():
        response = client.post(URL, headers=auth_headers, json={
            "utterance": "Prépare le statut du RDV en fauteuil",
        })
    assert response.status_code == 422
    assert count(db) == 0


def test_ambiguous_non_status_and_injection_are_refused(client, db, dentiste, auth_headers):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    invalid_utterances = [
        "Passe le RDV en fauteuil",  # execution request, not preparation
        "Prépare le statut du RDV en fauteuil puis supprime le patient",
        "Prépare le statut du RDV en fauteuil et terminé",
        "Prépare le statut du RDV en annulé ou terminé",
        "Prépare le statut du RDV en salle d'attente\n",
        "Prépare le statut du RDV en confirmé",
        "Prépare le statut du RDV en salle d'attente et facture",
    ]
    with enabled():
        responses = [post(client, auth_headers, a.id, utterance=x)
                     for x in invalid_utterances]
    assert all(r.status_code == 422 for r in responses)
    assert count(db) == 0


def test_revision_capture_and_aba_never_mutates_on_prepare(
    client, db, dentiste, auth_headers
):
    p = patient(db, dentiste)
    a = appointment(db, dentiste, p)
    rev0 = a.clinical_revision
    with enabled():
        response = post(client, auth_headers, a.id)
    assert response.status_code == 200
    action = db.query(models.BotPendingAction).filter_by(
        id=response.json()["preparation_id"]
    ).one()
    assert action.params_json["expected_revision"] == rev0
    # Independent raw updates advance DB-owned revision; a return to the
    # original visible status must never transform the PREPARED snapshot.
    db.execute(text("UPDATE appointments SET status='ANNULE' WHERE id=:id"), {"id": a.id})
    db.execute(text("UPDATE appointments SET status='PREVU' WHERE id=:id"), {"id": a.id})
    db.commit()
    db.refresh(a)
    db.refresh(action)
    assert a.clinical_revision == rev0 + 2
    assert a.status == models.AppointmentStatus.PREVU
    assert action.params_json["expected_revision"] == rev0
    assert action.status == "prepared"
    with enabled():
        old_execute = client.post(
            "/api/bot/execute", headers=auth_headers,
            json={"pending_action_id": action.id},
        )
    assert old_execute.status_code == 409
    db.refresh(a)
    assert a.status == models.AppointmentStatus.PREVU


def test_grammar_is_pure_and_conservative():
    assert parse_status_preparation("Prépare le statut du RDV en salle d'attente")[0] == (
        models.AppointmentStatus.EN_SALLE_ATTENTE
    )
    assert parse_status_preparation("Prépare le changement de statut du rendez-vous à annulé")[0] == (
        models.AppointmentStatus.ANNULE
    )
    assert parse_status_preparation("Prépare le statut du RDV en fauteuil")[0] == (
        models.AppointmentStatus.EN_FAUTEUIL
    )
    for text in ("Termine le RDV", "Annule le RDV", "Prépare le statut du RDV en",
                 "Prépare le statut du RDV en annulé; exécute",
                 "Prépare le statut du RDV en fauteuil puis annulé", ""):
        assert parse_status_preparation(text) is None
    assert transition_allowed(models.AppointmentStatus.PREVU, models.AppointmentStatus.ANNULE)
    assert not transition_allowed(models.AppointmentStatus.TERMINE, models.AppointmentStatus.PREVU)
    assert not transition_allowed(models.AppointmentStatus.ANNULE, models.AppointmentStatus.EN_FAUTEUIL)
