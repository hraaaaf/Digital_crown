from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend import models, schemas


ACTIVE_STATUSES = {"ACTIVE", "INTERRUPTED"}
TERMINAL_STATUSES = {"ABANDONED", "CLOSED"}

_ALLOWED_TRANSITIONS = {
    "ACTIVE": {"ENTER_PHASE", "INTERRUPT", "ABANDON", "CLOSE"},
    "INTERRUPTED": {"RESUME", "ABANDON", "CLOSE"},
    "ABANDONED": set(),
    "CLOSED": set(),
}


def get_ortho_case_by_id(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
):
    return (
        db.query(models.OrthoCase)
        .options(joinedload(models.OrthoCase.events))
        .filter(
            models.OrthoCase.id == case_id,
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
        )
        .first()
    )


def get_ortho_case(
    db: Session,
    patient_id: int,
    employer_id: int,
):
    active = (
        db.query(models.OrthoCase)
        .options(joinedload(models.OrthoCase.events))
        .filter(
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
            models.OrthoCase.lifecycle_status.in_(ACTIVE_STATUSES),
        )
        .order_by(models.OrthoCase.started_at.desc(), models.OrthoCase.id.desc())
        .first()
    )
    if active is not None:
        return active

    return (
        db.query(models.OrthoCase)
        .options(joinedload(models.OrthoCase.events))
        .filter(
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
        )
        .order_by(models.OrthoCase.started_at.desc(), models.OrthoCase.id.desc())
        .first()
    )


def create_ortho_case(
    db: Session,
    patient_id: int,
    employer_id: int,
    created_by: int,
    started_at: datetime,
    initial_phase_key: str | None,
):
    # Serialize creation per patient on PostgreSQL. This prevents two concurrent
    # requests from both observing "no active case" and creating duplicates.
    patient = (
        db.query(models.Patient)
        .filter(
            models.Patient.id == patient_id,
            models.Patient.employer_id == employer_id,
        )
        .with_for_update()
        .first()
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable.")

    existing = (
        db.query(models.OrthoCase)
        .filter(
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
            models.OrthoCase.lifecycle_status.in_(ACTIVE_STATUSES),
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Un traitement orthodontique actif ou interrompu existe déjà pour ce patient.",
        )

    case = models.OrthoCase(
        employer_id=employer_id,
        patient_id=patient_id,
        started_at=started_at,
        lifecycle_status="ACTIVE",
        current_phase_key=initial_phase_key,
        created_by=created_by,
    )
    db.add(case)
    db.flush()

    event = models.OrthoPhaseEvent(
        ortho_case_id=case.id,
        employer_id=employer_id,
        patient_id=patient_id,
        event_type="START",
        phase_key=initial_phase_key,
        effective_at=started_at,
        created_by=created_by,
    )
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(models.OrthoCase)
            .filter(
                models.OrthoCase.patient_id == patient_id,
                models.OrthoCase.employer_id == employer_id,
                models.OrthoCase.lifecycle_status.in_(ACTIVE_STATUSES),
            )
            .first()
        )
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="Un traitement orthodontique actif ou interrompu existe déjà pour ce patient.",
            )
        raise

    return get_ortho_case(db, patient_id, employer_id)


def transition_ortho_case(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
    created_by: int,
    event_type: str,
    effective_at: datetime,
    phase_key: str | None,
    note: str | None,
):
    case = (
        db.query(models.OrthoCase)
        .filter(
            models.OrthoCase.id == case_id,
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
        )
        .with_for_update()
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Traitement orthodontique introuvable.")

    allowed = _ALLOWED_TRANSITIONS.get(case.lifecycle_status, set())
    if event_type not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Transition {event_type} interdite depuis {case.lifecycle_status}.",
        )

    if event_type == "ENTER_PHASE" and phase_key is None:
        raise HTTPException(status_code=422, detail="phase_key est requis pour ENTER_PHASE.")
    if event_type != "ENTER_PHASE" and phase_key is not None:
        raise HTTPException(
            status_code=422,
            detail="phase_key est autorisé uniquement pour ENTER_PHASE.",
        )

    latest_event = (
        db.query(models.OrthoPhaseEvent)
        .filter(models.OrthoPhaseEvent.ortho_case_id == case.id)
        .order_by(
            models.OrthoPhaseEvent.effective_at.desc(),
            models.OrthoPhaseEvent.id.desc(),
        )
        .first()
    )
    if effective_at < case.started_at:
        raise HTTPException(
            status_code=409,
            detail="La transition ne peut pas précéder le début du traitement.",
        )
    if latest_event is not None and effective_at < latest_event.effective_at:
        raise HTTPException(
            status_code=409,
            detail="La transition ne peut pas précéder le dernier événement enregistré.",
        )

    if event_type == "ENTER_PHASE":
        case.current_phase_key = phase_key
    elif event_type == "INTERRUPT":
        case.lifecycle_status = "INTERRUPTED"
    elif event_type == "RESUME":
        case.lifecycle_status = "ACTIVE"
    elif event_type == "ABANDON":
        case.lifecycle_status = "ABANDONED"
        case.closed_at = effective_at
    elif event_type == "CLOSE":
        case.lifecycle_status = "CLOSED"
        case.closed_at = effective_at

    event = models.OrthoPhaseEvent(
        ortho_case_id=case.id,
        employer_id=employer_id,
        patient_id=patient_id,
        event_type=event_type,
        phase_key=phase_key,
        effective_at=effective_at,
        note=note,
        created_by=created_by,
    )
    db.add(event)
    db.commit()

    return get_ortho_case(db, patient_id, employer_id)


def list_ortho_controls(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
):
    return (
        db.query(models.OrthoControl)
        .filter(
            models.OrthoControl.ortho_case_id == case_id,
            models.OrthoControl.patient_id == patient_id,
            models.OrthoControl.employer_id == employer_id,
        )
        .order_by(models.OrthoControl.occurred_at.desc(), models.OrthoControl.id.desc())
        .all()
    )


def create_ortho_control(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
    created_by: int,
    occurred_at: datetime,
    phase_key: str | None,
    appointment_id: int | None,
    observations: str | None,
    appliance_context: str | None,
    notable_event: str | None,
    next_planned_step: str | None,
    next_control_at: datetime | None,
):
    case = (
        db.query(models.OrthoCase)
        .filter(
            models.OrthoCase.id == case_id,
            models.OrthoCase.patient_id == patient_id,
            models.OrthoCase.employer_id == employer_id,
        )
        .with_for_update()
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="Traitement orthodontique introuvable.")
    if case.lifecycle_status in TERMINAL_STATUSES:
        raise HTTPException(
            status_code=409,
            detail="Impossible d'ajouter un contrôle à un traitement orthodontique terminé.",
        )
    if occurred_at < case.started_at:
        raise HTTPException(
            status_code=409,
            detail="Le contrôle ne peut pas précéder le début du traitement.",
        )
    if next_control_at is not None and next_control_at < occurred_at:
        raise HTTPException(
            status_code=422,
            detail="next_control_at ne peut pas précéder occurred_at.",
        )

    if appointment_id is not None:
        appointment = (
            db.query(models.Appointment)
            .filter(
                models.Appointment.id == appointment_id,
                models.Appointment.patient_id == patient_id,
                models.Appointment.employer_id == employer_id,
            )
            .first()
        )
        if appointment is None:
            raise HTTPException(
                status_code=422,
                detail="Le rendez-vous référencé n'appartient pas à ce patient/cabinet.",
            )

    control = models.OrthoControl(
        ortho_case_id=case.id,
        employer_id=employer_id,
        patient_id=patient_id,
        appointment_id=appointment_id,
        occurred_at=occurred_at,
        phase_key=phase_key,
        observations=observations,
        appliance_context=appliance_context,
        notable_event=notable_event,
        next_planned_step=next_planned_step,
        next_control_at=next_control_at,
        created_by=created_by,
    )
    db.add(control)
    db.commit()
    db.refresh(control)
    return control
