"""Tests des évolutions CrownBot : CHANGE_STATUS réel + injection patient de session."""
from datetime import datetime, timedelta

from backend import models
from backend.services.bot.action_dispatcher import action_dispatcher
from backend.services.bot.intent_parser import ParsedIntent
from backend.tests.conftest import make_user


def _make_patient(db, owner):
    p = models.Patient(
        employer_id=owner.id, nom="Bennani", prenom="Ahmed",
        date_naissance=datetime(1990, 1, 1).date(), sexe="M",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _make_appt(db, owner, patient, when):
    a = models.Appointment(
        patient_id=patient.id, employer_id=owner.id,
        datetime_start=when, duration_minutes=30, motif="Contrôle",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def test_change_status_handler_then_execute(db):
    owner = make_user(db)
    patient = _make_patient(db, owner)
    appt = _make_appt(db, owner, patient, datetime.now().replace(hour=10, minute=0, second=0, microsecond=0))
    assert appt.status == models.AppointmentStatus.PREVU

    parsed = ParsedIntent(
        intent="CHANGE_STATUS", confidence=0.9,
        entities={"patient_id": patient.id},
        raw_message="marque le rdv de Ahmed comme terminé",
    )
    resp = action_dispatcher.dispatch(parsed, db, owner).to_dict()
    assert resp["action_type"] == "write_pending"
    pending = resp["pending_action"]
    assert pending["type"] == "CHANGE_STATUS"
    assert pending["params"]["status"] == "TERMINE"
    assert pending["params"]["appointment_id"] == appt.id

    # Exécution réelle
    exec_resp = action_dispatcher.execute(pending, db, owner).to_dict()
    assert exec_resp["action_type"] == "write_done"
    db.refresh(appt)
    assert appt.status == models.AppointmentStatus.TERMINE


def test_change_status_needs_status_clarification(db):
    owner = make_user(db)
    patient = _make_patient(db, owner)
    _make_appt(db, owner, patient, datetime.now().replace(hour=11, minute=0, second=0, microsecond=0))

    parsed = ParsedIntent(
        intent="CHANGE_STATUS", confidence=0.9,
        entities={"patient_id": patient.id},
        raw_message="change le statut du rdv",  # aucun statut cible
    )
    resp = action_dispatcher.dispatch(parsed, db, owner).to_dict()
    assert resp["action_type"] == "clarification"


def test_session_patient_injection_clears_clarification(db):
    """Sur un dossier patient, 'son dossier' sans nom doit utiliser le patient de session."""
    from backend.routers import bot
    owner = make_user(db)
    patient = _make_patient(db, owner)

    parsed, _ = bot._parse_and_authorize(
        message="affiche le dossier",  # QUERY_PATIENT sans patient cité
        context_window=[],
        current_user=owner,
        session_patient_id=patient.id,
    )
    # Le patient de session doit être injecté et la clarification levée
    assert parsed.entities.get("patient_id") == patient.id
    assert parsed.needs_clarification is False
