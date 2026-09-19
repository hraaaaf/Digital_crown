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


_F3_MEASUREMENTS = {
    "SNA": ("SNA", "deg"),
    "SNB": ("SNB", "deg"),
    "ANB": ("ANB", "deg"),
    "FMA": ("FMA", "deg"),
    "IMPA": ("IMPA", "deg"),
    "Inter_Incisif": ("Inter-incisif", "deg"),
    "I_Francfort": ("Incisive / Francfort", "deg"),
    "Angle_de_Tweed": ("Angle de Tweed", "deg"),
    "Angle_Nasolabial": ("Angle naso-labial", "deg"),
    "Surplomb": ("Surplomb", "mm"),
    "Recouvrement": ("Recouvrement", "mm"),
    "Wits": ("Wits", "mm"),
    "Decalage_A_B": ("Décalage A-B", "mm"),
    "Situation_A": ("Situation A", "mm"),
    "Situation_B": ("Situation B", "mm"),
    "Profondeur_Faciale": ("Profondeur faciale", "deg"),
    "Ligne_E_Ls": ("Ligne E lèvre sup.", "mm"),
    "Ligne_E_Li": ("Ligne E lèvre inf.", "mm"),
}


def _numeric_value(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        candidate = value.get("valeur")
        if isinstance(candidate, bool):
            return None
        if isinstance(candidate, (int, float)):
            return float(candidate)
    return None


def _extract_f3_measurements(payload: dict | None) -> dict[str, float]:
    found: dict[str, float] = {}

    def visit(node):
        if not isinstance(node, dict):
            return
        for key, value in node.items():
            if key in _F3_MEASUREMENTS and key not in found:
                numeric = _numeric_value(value)
                if numeric is not None:
                    found[key] = numeric
            if isinstance(value, dict):
                visit(value)

    visit(payload or {})
    return found


def _f3_timepoint_or_404(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
    ordinal: int,
):
    timepoint = (
        db.query(models.OrthoTimepoint)
        .options(joinedload(models.OrthoTimepoint.evidences))
        .filter(
            models.OrthoTimepoint.ortho_case_id == case_id,
            models.OrthoTimepoint.patient_id == patient_id,
            models.OrthoTimepoint.employer_id == employer_id,
            models.OrthoTimepoint.ordinal == ordinal,
        )
        .first()
    )
    if timepoint is None:
        raise HTTPException(status_code=404, detail=f"Timepoint T{ordinal} introuvable.")
    return timepoint


def _f3_evidence_summaries(db: Session, timepoint, patient_id: int, employer_id: int):
    summaries = []
    for evidence in timepoint.evidences:
        if evidence.clinical_asset_id is not None:
            asset = (
                db.query(ClinicalAsset)
                .filter(
                    ClinicalAsset.id == evidence.clinical_asset_id,
                    ClinicalAsset.patient_id == patient_id,
                    ClinicalAsset.employer_id == employer_id,
                )
                .first()
            )
            if asset is not None:
                summaries.append(
                    schemas.OrthoCompareEvidenceOut(
                        kind="CLINICAL_ASSET",
                        ref_id=asset.id,
                        recorded_at=asset.captured_at or asset.created_at,
                        label=asset.asset_type,
                    )
                )
        elif evidence.cephalo_analysis_id is not None:
            ceph = (
                db.query(models.CephaloAnalysis)
                .filter(
                    models.CephaloAnalysis.id == evidence.cephalo_analysis_id,
                    models.CephaloAnalysis.patient_id == patient_id,
                )
                .first()
            )
            if ceph is not None:
                summaries.append(
                    schemas.OrthoCompareEvidenceOut(
                        kind="CEPHALO",
                        ref_id=ceph.id,
                        recorded_at=ceph.created_at,
                        label="Céphalométrie calibrée" if ceph.is_calibrated else "Céphalométrie non calibrée",
                    )
                )
        elif evidence.panoramic_analysis_id is not None:
            pano = (
                db.query(models.PanoramicAnalysis)
                .filter(
                    models.PanoramicAnalysis.id == evidence.panoramic_analysis_id,
                    models.PanoramicAnalysis.patient_id == patient_id,
                )
                .first()
            )
            if pano is not None:
                summaries.append(
                    schemas.OrthoCompareEvidenceOut(
                        kind="PANORAMIC",
                        ref_id=pano.id,
                        recorded_at=pano.created_at,
                        label="Panoramique",
                    )
                )
    return summaries


def compare_ortho_timepoints(
    db: Session,
    patient_id: int,
    case_id: int,
    employer_id: int,
    from_ordinal: int,
    to_ordinal: int,
):
    if from_ordinal == to_ordinal:
        raise HTTPException(status_code=422, detail="Deux timepoints distincts sont requis.")

    case = get_ortho_case_by_id(db, patient_id, case_id, employer_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Traitement orthodontique introuvable.")

    left = _f3_timepoint_or_404(db, patient_id, case_id, employer_id, from_ordinal)
    right = _f3_timepoint_or_404(db, patient_id, case_id, employer_id, to_ordinal)

    def cephalo_rows(timepoint):
        ids = [
            e.cephalo_analysis_id
            for e in timepoint.evidences
            if e.cephalo_analysis_id is not None
        ]
        if not ids:
            return []
        return (
            db.query(models.CephaloAnalysis)
            .filter(
                models.CephaloAnalysis.id.in_(ids),
                models.CephaloAnalysis.patient_id == patient_id,
            )
            .all()
        )

    left_ceph = cephalo_rows(left)
    right_ceph = cephalo_rows(right)
    measurements = []
    measurement_status = "NO_CEPHALO_PAIR"

    if len(left_ceph) == 1 and len(right_ceph) == 1:
        left_values = _extract_f3_measurements(left_ceph[0].angles_data)
        right_values = _extract_f3_measurements(right_ceph[0].angles_data)
        both_calibrated = bool(left_ceph[0].is_calibrated and right_ceph[0].is_calibrated)

        for key, (label, unit) in _F3_MEASUREMENTS.items():
            if key not in left_values or key not in right_values:
                continue
            if unit == "mm" and not both_calibrated:
                continue
            from_value = left_values[key]
            to_value = right_values[key]
            measurements.append(
                schemas.OrthoMeasurementDeltaOut(
                    key=key,
                    label=label,
                    unit=unit,
                    from_value=from_value,
                    to_value=to_value,
                    delta=round(to_value - from_value, 4),
                )
            )

        if measurements:
            measurement_status = (
                "AVAILABLE"
                if both_calibrated
                else "AVAILABLE_ANGULAR_ONLY_LINEAR_UNCALIBRATED"
            )
        else:
            measurement_status = "NO_COMMON_MEASUREMENTS"
    elif len(left_ceph) > 1 or len(right_ceph) > 1:
        measurement_status = "AMBIGUOUS_CEPHALO_PAIR"

    return schemas.OrthoLongitudinalCompareOut(
        patient_id=patient_id,
        ortho_case_id=case_id,
        from_timepoint=schemas.OrthoCompareTimepointOut(
            id=left.id,
            ordinal=left.ordinal,
            occurred_at=left.occurred_at,
            note=left.note,
            evidences=_f3_evidence_summaries(db, left, patient_id, employer_id),
        ),
        to_timepoint=schemas.OrthoCompareTimepointOut(
            id=right.id,
            ordinal=right.ordinal,
            occurred_at=right.occurred_at,
            note=right.note,
            evidences=_f3_evidence_summaries(db, right, patient_id, employer_id),
        ),
        measurements=measurements,
        measurement_status=measurement_status,
    )


def build_ortho_cockpit(
    db: Session,
    patient_id: int,
    employer_id: int,
):
    case = get_ortho_case(db, patient_id, employer_id)
    if case is None:
        return schemas.OrthoCockpitOut(patient_id=patient_id)

    controls = list_ortho_controls(db, patient_id, case.id, employer_id)
    latest_control = controls[0] if controls else None

    timepoints = (
        db.query(models.OrthoTimepoint)
        .options(joinedload(models.OrthoTimepoint.evidences))
        .filter(
            models.OrthoTimepoint.ortho_case_id == case.id,
            models.OrthoTimepoint.patient_id == patient_id,
            models.OrthoTimepoint.employer_id == employer_id,
        )
        .order_by(
            models.OrthoTimepoint.ordinal.desc(),
            models.OrthoTimepoint.occurred_at.desc(),
            models.OrthoTimepoint.id.desc(),
        )
        .all()
    )
    latest_timepoint = timepoints[0] if timepoints else None

    next_appointment = (
        db.query(models.Appointment)
        .filter(
            models.Appointment.patient_id == patient_id,
            models.Appointment.employer_id == employer_id,
            models.Appointment.deleted_at.is_(None),
            models.Appointment.datetime_start >= datetime.now(),
            models.Appointment.status.in_(
                [
                    models.AppointmentStatus.PREVU,
                    models.AppointmentStatus.EN_SALLE_ATTENTE,
                    models.AppointmentStatus.EN_FAUTEUIL,
                    models.AppointmentStatus.CONFIRME,
                ]
            ),
        )
        .order_by(models.Appointment.datetime_start.asc(), models.Appointment.id.asc())
        .first()
    )

    latest_by_kind = {
        "CEPHALO": None,
        "PANORAMIC": None,
        "CLINICAL_ASSET": None,
    }
    for timepoint in timepoints:
        for evidence in _f3_evidence_summaries(db, timepoint, patient_id, employer_id):
            if latest_by_kind.get(evidence.kind) is None:
                latest_by_kind[evidence.kind] = schemas.OrthoCockpitEvidenceOut(
                    kind=evidence.kind,
                    ref_id=evidence.ref_id,
                    recorded_at=evidence.recorded_at,
                    label=evidence.label,
                    timepoint_ordinal=timepoint.ordinal,
                )
        if all(latest_by_kind.values()):
            break

    attention: list[str] = []
    if case.lifecycle_status == "INTERRUPTED":
        attention.append("TREATMENT_INTERRUPTED")
    if latest_timepoint is None:
        attention.append("NO_TIMEPOINT")
    elif not latest_timepoint.evidences:
        attention.append("LATEST_TIMEPOINT_WITHOUT_EVIDENCE")
    if latest_control is None or latest_control.next_control_at is None:
        attention.append("NO_NEXT_CONTROL_DATE")
    if latest_control is not None and latest_control.next_planned_step:
        attention.append("NEXT_PLANNED_STEP_PRESENT")

    return schemas.OrthoCockpitOut(
        patient_id=patient_id,
        case=schemas.OrthoCockpitCaseOut(
            case_id=case.id,
            started_at=case.started_at,
            lifecycle_status=case.lifecycle_status,
            current_phase_key=case.current_phase_key,
            closed_at=case.closed_at,
            controls_count=len(controls),
        ),
        latest_control=(
            schemas.OrthoCockpitControlOut(
                id=latest_control.id,
                occurred_at=latest_control.occurred_at,
                phase_key=latest_control.phase_key,
                notable_event=latest_control.notable_event,
                next_planned_step=latest_control.next_planned_step,
                next_control_at=latest_control.next_control_at,
                appointment_id=latest_control.appointment_id,
            )
            if latest_control is not None
            else None
        ),
        next_appointment=(
            schemas.OrthoCockpitAppointmentOut(
                id=next_appointment.id,
                datetime_start=next_appointment.datetime_start,
                status=(
                    next_appointment.status.value
                    if hasattr(next_appointment.status, "value")
                    else str(next_appointment.status)
                ),
                motif=next_appointment.motif,
            )
            if next_appointment is not None
            else None
        ),
        latest_timepoint=(
            schemas.OrthoCockpitTimepointOut(
                id=latest_timepoint.id,
                ordinal=latest_timepoint.ordinal,
                occurred_at=latest_timepoint.occurred_at,
                note=latest_timepoint.note,
                evidence_count=len(latest_timepoint.evidences),
            )
            if latest_timepoint is not None
            else None
        ),
        latest_cephalo=latest_by_kind["CEPHALO"],
        latest_panoramic=latest_by_kind["PANORAMIC"],
        latest_clinical_asset=latest_by_kind["CLINICAL_ASSET"],
        attention=attention,
    )
