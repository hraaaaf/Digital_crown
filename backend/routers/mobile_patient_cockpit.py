"""Read-only patient cockpit for the paired mobile PWA.

The endpoint deliberately exposes only the data needed for a sub-30-second chairside
flow. Clinical/financial data remains tenant-scoped, permission-gated and encrypted.
"""
from datetime import datetime, timedelta
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import insert, or_
from sqlalchemy.orm import Session

from backend import database, models
from backend.routers.auth import has_permission
from backend.routers.mobile import _role_name
from backend.routers import mobile_legacy as _legacy
from backend.routers.mobile_legacy import require_mobile_permission
from backend.routers.mobile_resource_bridge import (
    BRIDGE_CONTEXT_TABLE,
    _document_permission,
    _purge_expired,
    _resource_entity,
    _resource_label,
    _resource_token,
)
from backend.routers.patient_financial_p6 import get_patient_financial_snapshot_p6
from backend.services.zka_crypto import encrypt_payload

router = APIRouter()


class PatientCockpitContextRequest(BaseModel):
    resource_type: str = 'patient'
    resource_id: int | None = None


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


def _resource_patient_id(resource_type: str, resource) -> int:
    if resource_type == 'patient':
        return int(resource.id)
    patient_id = getattr(resource, 'patient_id', None)
    if patient_id is None:
        raise HTTPException(status_code=404, detail="Ressource sans patient associé.")
    return int(patient_id)


def _unique_manual_code(db: Session, now: datetime) -> str:
    for _ in range(20):
        candidate = f"{secrets.randbelow(900000) + 100000:06d}"
        collision = db.query(models.ZKAPairingToken).filter(
            models.ZKAPairingToken.manual_code == candidate,
            models.ZKAPairingToken.used_at.is_(None),
            models.ZKAPairingToken.expires_at > now,
        ).first()
        if collision is None:
            return candidate
    raise HTTPException(status_code=503, detail="Impossible de générer un contexte mobile unique.")


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


@router.get('/patient-cockpit/{patient_id}/resources', summary='Ressources ouvrables depuis le cockpit patient')
def get_mobile_patient_cockpit_resources(
    patient_id: int,
    db: Session = Depends(database.get_db),
    mobile_user: models.User = Depends(require_mobile_permission('patients')),
):
    employer_id = mobile_user.get_employer_id()
    _patient_or_404(db, employer_id, patient_id)

    documents = []
    candidates = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
    ).order_by(models.DocumentArchive.id.desc()).limit(12).all()
    for document in candidates:
        permission = _document_permission(document)
        if not has_permission(mobile_user, permission):
            continue
        documents.append({
            'id': document.id,
            'label': str(getattr(document, 'name', None) or getattr(document, 'title', None) or f'Document #{document.id}'),
            'document_type': str(getattr(getattr(document, 'document_type', None), 'value', getattr(document, 'document_type', '')) or ''),
            'created_at': document.created_at.isoformat() if getattr(document, 'created_at', None) else None,
        })

    panoramics = []
    if has_permission(mobile_user, 'panoramic'):
        candidates = db.query(models.PanoramicAnalysis).filter(
            models.PanoramicAnalysis.patient_id == patient_id,
        ).order_by(models.PanoramicAnalysis.id.desc()).limit(12).all()
        for analysis in candidates:
            try:
                _resource_entity(db, mobile_user, 'panoramic', int(analysis.id))
            except HTTPException as exc:
                if exc.status_code in (403, 404):
                    continue
                raise
            panoramics.append({
                'id': analysis.id,
                'label': f'Panoramique #{analysis.id}',
                'created_at': analysis.created_at.isoformat() if getattr(analysis, 'created_at', None) else None,
            })

    return encrypt_payload({'documents': documents, 'panoramics': panoramics})


@router.post('/patient-cockpit/{patient_id}/context', summary='Ouvrir un contexte clinique opaque depuis le cockpit patient')
def create_mobile_patient_cockpit_context(
    patient_id: int,
    body: PatientCockpitContextRequest,
    authorization: str = Header(...),
    db: Session = Depends(database.get_db),
):
    mobile_user, tenant_id, mobile_payload = _legacy._decode_mobile_identity(authorization, db)
    if not has_permission(mobile_user, 'patients'):
        raise HTTPException(status_code=403, detail="Accès patient mobile refusé.")
    _patient_or_404(db, tenant_id, patient_id)

    resource_type = body.resource_type.strip().lower()
    if resource_type not in {'patient', 'document', 'panoramic'}:
        raise HTTPException(status_code=422, detail="Contexte Patient Cockpit non pris en charge.")
    resource_id = patient_id if resource_type == 'patient' else body.resource_id
    if not resource_id:
        raise HTTPException(status_code=422, detail="Ressource mobile manquante.")

    resource = _resource_entity(db, mobile_user, resource_type, int(resource_id))
    if _resource_patient_id(resource_type, resource) != int(patient_id):
        raise HTTPException(status_code=404, detail="Cette ressource n’appartient pas au patient sélectionné.")

    device_id = str(mobile_payload.get('device_id') or '')
    if not device_id:
        raise HTTPException(status_code=401, detail="Session mobile sans appareil associé.")

    config = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == tenant_id).first()
    master_key = os.getenv('CABINET_MASTER_KEY_HEX')
    if not config or not master_key:
        raise HTTPException(status_code=404, detail="Configuration ZKA incomplète.")

    now = datetime.utcnow()
    _purge_expired(db, tenant_id, now)
    record = models.ZKAPairingToken(
        token=_resource_token(),
        manual_code=_unique_manual_code(db, now),
        employer_id=tenant_id,
        user_id=mobile_user.id,
        public_id=config.public_id,
        master_key=master_key,
        role=_role_name(mobile_user),
        # Cleanup horizon for orphaned contexts. Existing M4 context validation does
        # not promise a user-facing TTL after a context has already been resolved.
        expires_at=now + timedelta(minutes=30),
        used_at=now,
    )
    db.add(record)
    db.flush()

    context_key = secrets.token_urlsafe(24)
    db.execute(insert(BRIDGE_CONTEXT_TABLE).values(
        context_key=context_key,
        pairing_id=record.id,
        employer_id=tenant_id,
        target_user_id=mobile_user.id,
        device_id=device_id,
        resource_type=resource_type,
        resource_id=int(resource_id),
        created_at=now,
    ))
    db.commit()

    return {
        'context': {
            'type': resource_type,
            'key': context_key,
            'state': 'ready',
        },
        'resource_label': _resource_label(resource_type),
        'contains_patient_data': False,
        'contains_resource_data': False,
    }


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
