"""Read-only patient cockpit for the paired mobile PWA.

The endpoint deliberately exposes only the data needed for a sub-30-second chairside
flow. Clinical/financial data remains tenant-scoped, permission-gated and encrypted.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import has_permission
from backend.routers.mobile_legacy import require_mobile_permission
from backend.routers.patient_financial_p6 import get_patient_financial_snapshot_p6
from backend.services.zka_crypto import encrypt_payload

router = APIRouter()


def _patient_or_404(db: Session, employer_id: int, patient_id: int) -> models.Patient:
    patient = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.employer_id == employer_id,
        models.Patient.deleted_at.is_(None),
    ).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient introuvable dans ce cabinet.")
    return patient


def _patient_name(patient: models.Patient) -> str:
    return f"{patient.prenom or ''} {patient.nom or ''}".strip()


def _has_medical_alert(patient: models.Patient) -> bool:
    return bool((patient.antecedents_medicaux or '').strip())


@router.get('/patient-cockpit/search', summary='Recherche patient rapide pour le cockpit mobile')
def search_mobile_patient_cockpit(
    q: str = Query(default='', max_length=120),
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(require_mobile_permission('patients')),
):
    employer_id = mobile_user.get_employer_id()
    query = db.query(models.Patient).filter(
        models.Patient.employer_id == employer_id,
        models.Patient.deleted_at.is_(None),
    )

    normalized = q.strip()
    if normalized:
        pattern = f"%{normalized}%"
        query = query.filter(or_(
            models.Patient.prenom.ilike(pattern),
            models.Patient.nom.ilike(pattern),
            models.Patient.telephone.ilike(pattern),
            models.Patient.numero_dossier.ilike(pattern),
        ))

    patients = query.order_by(models.Patient.prenom.asc(), models.Patient.nom.asc()).limit(25).all()
    return encrypt_payload({
        'patients': [
            {
                'id': patient.id,
                'name': _patient_name(patient),
                'phone': patient.telephone,
                'numero_dossier': patient.numero_dossier,
                'has_medical_alert': _has_medical_alert(patient),
            }
            for patient in patients
        ]
    })


@router.get('/patient-cockpit/{patient_id}', summary='Cockpit patient mobile en lecture seule')
def get_mobile_patient_cockpit(
    patient_id: int,
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(require_mobile_permission('patients')),
):
    employer_id = mobile_user.get_employer_id()
    patient = _patient_or_404(db, employer_id, patient_id)

    next_appointment = db.query(models.Appointment).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.patient_id == patient.id,
        models.Appointment.datetime_start >= datetime.now(),
        models.Appointment.status != models.AppointmentStatus.ANNULE,
    ).order_by(models.Appointment.datetime_start.asc()).first()

    finance = None
    if has_permission(mobile_user, ['accounting', 'payments']):
        snapshot = get_patient_financial_snapshot_p6(patient.id, db, mobile_user)
        finance = {
            'has_billing_data': snapshot['has_billing_data'],
            'remaining_due': snapshot['remaining_due'],
            'total_collected': snapshot['total_collected'],
            'overdue_count': snapshot['overdue_count'],
        }

    medical_summary = (patient.antecedents_medicaux or '').strip() or None
    return encrypt_payload({
        'patient': {
            'id': patient.id,
            'name': _patient_name(patient),
            'prenom': patient.prenom,
            'nom': patient.nom,
            'numero_dossier': patient.numero_dossier,
            'date_naissance': patient.date_naissance.isoformat() if patient.date_naissance else None,
            'phone': patient.telephone,
            'assurance': patient.assurance,
            'has_medical_alert': bool(medical_summary),
            'medical_alert_summary': medical_summary,
        },
        'next_appointment': None if next_appointment is None else {
            'id': next_appointment.id,
            'datetime_start': next_appointment.datetime_start.isoformat(),
            'duration_minutes': next_appointment.duration_minutes,
            'motif': next_appointment.motif or 'Consultation',
            'status': getattr(next_appointment.status, 'value', next_appointment.status),
        },
        'finance': finance,
    })
