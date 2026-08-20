from datetime import datetime, timedelta

from backend import models, schemas
from backend.services import patient_journey_service


def _make_patient(db, owner):
    patient = models.Patient(
        nom="JOURNEY",
        prenom="Test",
        date_naissance=datetime(1990, 1, 1),
        sexe="M",
        employer_id=owner.id,
        assurance="AUCUNE",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def test_p2_financial_summary_is_neutral_without_billing_rows(db, dentiste):
    patient = _make_patient(db, dentiste)

    summary = patient_journey_service._build_summary(db, patient.id)

    assert summary.has_billing_data is False
    assert summary.remaining_due == 0.0
    assert summary.total_plan_steps == 0
    assert summary.active_plan_steps == 0


def test_p2_plan_step_keeps_master_plan_as_source_and_navigation_target(db, dentiste):
    patient = _make_patient(db, dentiste)
    plan = models.TreatmentMasterPlan(patient_id=patient.id)
    db.add(plan)
    db.flush()
    step = models.TreatmentPlanStep(
        plan_id=plan.id,
        title="Contrôle prothétique",
        assistant="general",
        status=models.PlanStatus.PENDING,
        date_str="2026-08-19",
        order_index=0,
    )
    db.add(step)
    db.commit()
    db.refresh(step)

    events = patient_journey_service._collect_events(db, patient.id, since=None)
    event = next(e for e in events if e.event_key == f"treatment_plan_step:{step.id}")

    assert event.source == "treatment_plan_step"
    assert event.ref_id == step.id
    assert event.title == "Contrôle prothétique"
    assert event.status == models.PlanStatus.PENDING.value
    assert event.navigation_target == schemas.NavigationTarget.TREATMENT_PLAN_TAB


def test_p2_next_appointment_is_real_agenda_datetime(db, dentiste):
    patient = _make_patient(db, dentiste)
    future = datetime.now().replace(microsecond=0) + timedelta(days=3)
    appointment = models.Appointment(
        patient_id=patient.id,
        patient_name="JOURNEY Test",
        datetime_start=future,
        duration_minutes=30,
        motif="Contrôle",
        status=models.AppointmentStatus.CONFIRME,
        employer_id=dentiste.id,
    )
    db.add(appointment)
    db.commit()

    summary = patient_journey_service._build_summary(db, patient.id)

    assert summary.next_appointment == future
