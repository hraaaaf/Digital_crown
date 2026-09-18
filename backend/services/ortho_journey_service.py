from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend import models, schemas
from backend.models_media_core import ClinicalAsset


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
    note: str | None,
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
        note=note,
        next_control_at=next_control_at,
        created_by=created_by,
    )
    db.add(control)
    db.commit()
    db.refresh(control)
    return control


def list_ortho_timepoints(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
):
    return (
        db.query(models.OrthoTimepoint)
        .options(joinedload(models.OrthoTimepoint.evidences))
        .filter(
            models.OrthoTimepoint.ortho_case_id == case_id,
            models.OrthoTimepoint.patient_id == patient_id,
            models.OrthoTimepoint.employer_id == employer_id,
        )
        .order_by(models.OrthoTimepoint.ordinal.asc())
        .all()
    )


def create_ortho_timepoint(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
    created_by: int,
    ordinal: int,
    occurred_at: datetime,
    note: str | None,
):
    case = get_ortho_case_by_id(db, patient_id, case_id, employer_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Traitement orthodontique introuvable.")
    if occurred_at < case.started_at:
        raise HTTPException(
            status_code=409,
            detail="Le timepoint ne peut pas précéder le début du traitement.",
        )

    existing = (
        db.query(models.OrthoTimepoint)
        .filter(
            models.OrthoTimepoint.ortho_case_id == case_id,
            models.OrthoTimepoint.ordinal == ordinal,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Le timepoint T{ordinal} existe déjà pour ce traitement.",
        )

    timepoint = models.OrthoTimepoint(
        ortho_case_id=case_id,
        employer_id=employer_id,
        patient_id=patient_id,
        ordinal=ordinal,
        occurred_at=occurred_at,
        note=note,
        created_by=created_by,
    )
    db.add(timepoint)
    db.commit()
    db.refresh(timepoint)
    return timepoint


def add_ortho_timepoint_evidence(
    db: Session,
    patient_id: int,
    case_id: int,
    timepoint_id: int,
    employer_id: int,
    created_by: int,
    clinical_asset_id: int | None,
    cephalo_analysis_id: int | None,
    panoramic_analysis_id: int | None,
):
    timepoint = (
        db.query(models.OrthoTimepoint)
        .filter(
            models.OrthoTimepoint.id == timepoint_id,
            models.OrthoTimepoint.ortho_case_id == case_id,
            models.OrthoTimepoint.patient_id == patient_id,
            models.OrthoTimepoint.employer_id == employer_id,
        )
        .with_for_update()
        .first()
    )
    if timepoint is None:
        raise HTTPException(status_code=404, detail="Timepoint orthodontique introuvable.")

    supplied = [
        clinical_asset_id is not None,
        cephalo_analysis_id is not None,
        panoramic_analysis_id is not None,
    ]
    if sum(supplied) != 1:
        raise HTTPException(status_code=422, detail="Une seule source canonique doit être référencée.")

    if clinical_asset_id is not None:
        asset = (
            db.query(ClinicalAsset)
            .filter(
                ClinicalAsset.id == clinical_asset_id,
                ClinicalAsset.patient_id == patient_id,
                ClinicalAsset.employer_id == employer_id,
            )
            .first()
        )
        if asset is None:
            raise HTTPException(status_code=422, detail="Média clinique introuvable pour ce patient/cabinet.")
        if asset.timepoint and asset.timepoint != f"T{timepoint.ordinal}":
            raise HTTPException(
                status_code=409,
                detail=f"Le média est déjà étiqueté {asset.timepoint}, incompatible avec T{timepoint.ordinal}.",
            )

    if cephalo_analysis_id is not None:
        cephalo = (
            db.query(models.CephaloAnalysis)
            .filter(
                models.CephaloAnalysis.id == cephalo_analysis_id,
                models.CephaloAnalysis.patient_id == patient_id,
            )
            .first()
        )
        if cephalo is None:
            raise HTTPException(status_code=422, detail="Analyse céphalométrique introuvable pour ce patient.")

    if panoramic_analysis_id is not None:
        pano = (
            db.query(models.PanoramicAnalysis)
            .filter(
                models.PanoramicAnalysis.id == panoramic_analysis_id,
                models.PanoramicAnalysis.patient_id == patient_id,
            )
            .first()
        )
        if pano is None:
            raise HTTPException(status_code=422, detail="Analyse panoramique introuvable pour ce patient.")

    duplicate_q = db.query(models.OrthoTimepointEvidence)
    if clinical_asset_id is not None:
        duplicate_q = duplicate_q.filter(models.OrthoTimepointEvidence.clinical_asset_id == clinical_asset_id)
    elif cephalo_analysis_id is not None:
        duplicate_q = duplicate_q.filter(models.OrthoTimepointEvidence.cephalo_analysis_id == cephalo_analysis_id)
    else:
        duplicate_q = duplicate_q.filter(models.OrthoTimepointEvidence.panoramic_analysis_id == panoramic_analysis_id)
    if duplicate_q.first() is not None:
        raise HTTPException(status_code=409, detail="Cette preuve est déjà liée à un timepoint orthodontique.")

    evidence = models.OrthoTimepointEvidence(
        ortho_timepoint_id=timepoint_id,
        employer_id=employer_id,
        patient_id=patient_id,
        clinical_asset_id=clinical_asset_id,
        cephalo_analysis_id=cephalo_analysis_id,
        panoramic_analysis_id=panoramic_analysis_id,
        created_by=created_by,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence
