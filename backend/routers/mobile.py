"""
Routes PWA Mobile â€” LAN-first, zÃ©ro cloud.
Aucune donnÃ©e ne sort du rÃ©seau local du cabinet.
"""
import uuid
import socket
import os
from datetime import datetime, date, timedelta, time as dt_time, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Body
from sqlalchemy import func, extract
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from jose import jwt, JWTError

from backend import models, database
from backend.security import SECRET_KEY, ALGORITHM

router = APIRouter(tags=["Mobile ZKA"])


# â”€â”€ HELPERS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _create_mobile_jwt(employer_id: int, role: str) -> str:
    """JWT mobile Ã  365 jours â€” type=mobile pour isolation des routes rÃ©guliÃ¨res."""
    payload = {
        "sub": str(employer_id),
        "type": "mobile",
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(days=365),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_mobile_employer_id(authorization: str = Header(...)) -> int:
    """DÃ©pendance : valide le JWT mobile et retourne l'employer_id."""
    err = HTTPException(status_code=401, detail="Token mobile invalide ou expirÃ©.")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise err
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "mobile":
            raise err
        return int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise err

def get_mobile_role(authorization: str = Header(...)) -> str:
    """DÃ©pendance : valide le JWT mobile et retourne le role."""
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() == "bearer":
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("role", "DENTISTE")
    except Exception:
        pass
    return "DENTISTE"


def get_lan_base_url() -> str:
    """
    Retourne l'URL LAN du serveur.
    FRONTEND_URL override explicite si non-localhost.
    Sinon, auto-dÃ©tection IP LAN via socket UDP.
    """
    configured = os.getenv("FRONTEND_URL", "").rstrip("/")
    if configured and "localhost" not in configured and "127.0.0.1" not in configured:
        return configured
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        port = os.getenv("PORT", "8005")
        return f"http://{lan_ip}:{port}"
    except Exception:
        return configured or "http://localhost:8005"


# â”€â”€ PING â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/ping", summary="VÃ©rification de connectivitÃ© LAN")
def ping():
    return {"status": "ok", "mode": "lan"}


# â”€â”€ CLAIM TOKEN â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class ClaimTokenRequest(BaseModel):
    token: str


@router.post(
    "/claim-token",
    summary="Ã‰changer un token Ã©phÃ©mÃ¨re QR contre un JWT mobile",
    description="Token Ã  usage unique (UUID 5 min). Retourne publicId, masterKey et un JWT mobile 24h.",
)
def claim_pairing_token(
    body: ClaimTokenRequest,
    db: Session = Depends(database.get_db),
):
    record = (
        db.query(models.ZKAPairingToken)
        .filter(
            models.ZKAPairingToken.token == body.token,
            models.ZKAPairingToken.used_at == None,  # noqa: E711
            models.ZKAPairingToken.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Token invalide, expirÃ© ou dÃ©jÃ  utilisÃ©.")

    record.used_at = datetime.utcnow()
    role = getattr(record, "role", "DENTISTE")
    db.commit()

    return {
        "publicId": record.public_id,
        "masterKey": record.master_key,
        "role": role,
        "access_token": _create_mobile_jwt(record.employer_id, role),
    }


# â”€â”€ SNAPSHOT LAN-FIRST â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get(
    "/snapshot",
    summary="Snapshot temps rÃ©el du cabinet â€” LAN uniquement",
    description="Retourne agenda du jour, KPIs financiers et liste rouge. DonnÃ©es 100% locales.",
)
def get_mobile_snapshot(
    target_date: str = None,
    employer_id: int = Depends(get_mobile_employer_id),
    role: str = Depends(get_mobile_role),
    db: Session = Depends(database.get_db),
):
    if target_date:
        today = datetime.strptime(target_date, "%Y-%m-%d").date()
    else:
        today = date.today()
    day_start = datetime.combine(today, dt_time.min)
    day_end = datetime.combine(today, dt_time.max)

    # â”€â”€ Agenda du jour â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    apts = (
        db.query(models.Appointment)
        .options(joinedload(models.Appointment.patient))
        .filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.datetime_start >= day_start,
            models.Appointment.datetime_start <= day_end,
            models.Appointment.status != models.AppointmentStatus.ANNULE,
        )
        .order_by(models.Appointment.datetime_start)
        .all()
    )

    appointments = [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "time": a.datetime_start.strftime("%H:%M"),
            "patient_name": (
                f"{a.patient.prenom} {a.patient.nom}"
                if a.patient else (a.patient_name or "Patient inconnu")
            ),
            "phone": a.patient.telephone if a.patient else None,
            "motif": a.motif or "Consultation",
            "status": a.status.value if a.status else None,
            "duration_minutes": a.duration_minutes,
        }
        for a in apts
    ]

    # ──────────────────────────────────────────────────────────────────────────────────────────────────
    today_revenue = (
        db.query(func.sum(models.Payment.amount))
        .join(models.Patient, models.Payment.patient_id == models.Patient.id)
        .filter(
            models.Patient.employer_id == employer_id,
            models.Payment.payment_date >= day_start,
            models.Payment.payment_date <= day_end,
        )
        .scalar() or 0.0
    )

    # â”€â”€ Recettes du mois courant â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    month_revenue = (
        db.query(func.sum(models.Payment.amount))
        .join(models.Patient, models.Payment.patient_id == models.Patient.id)
        .filter(
            models.Patient.employer_id == employer_id,
            extract("year", models.Payment.payment_date) == today.year,
            extract("month", models.Payment.payment_date) == today.month,
        )
        .scalar() or 0.0
    )

    # â”€â”€ Variation mois prÃ©cÃ©dent â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    last_month_last_day = today.replace(day=1) - timedelta(days=1)
    prev_month_revenue = (
        db.query(func.sum(models.Payment.amount))
        .join(models.Patient, models.Payment.patient_id == models.Patient.id)
        .filter(
            models.Patient.employer_id == employer_id,
            extract("year", models.Payment.payment_date) == last_month_last_day.year,
            extract("month", models.Payment.payment_date) == last_month_last_day.month,
        )
        .scalar() or 0.0
    )

    month_variation = None
    if prev_month_revenue > 0:
        month_variation = round(
            ((month_revenue - prev_month_revenue) / prev_month_revenue) * 100, 1
        )

    # â”€â”€ Recettes 7 derniers jours â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    week_start = datetime.combine(today - timedelta(days=6), dt_time.min)
    weekly_rows = (
        db.query(
            func.date(models.Payment.payment_date).label("day"),
            func.sum(models.Payment.amount).label("total"),
        )
        .join(models.Patient, models.Payment.patient_id == models.Patient.id)
        .filter(
            models.Patient.employer_id == employer_id,
            models.Payment.payment_date >= week_start,
        )
        .group_by(func.date(models.Payment.payment_date))
        .all()
    )
    weekly_map = {str(r.day): float(r.total) for r in weekly_rows}
    weekly_revenue = [
        {"date": str(today - timedelta(days=6 - i)), "amount": weekly_map.get(str(today - timedelta(days=6 - i)), 0.0)}
        for i in range(7)
    ]

    # â”€â”€ Nombre total patients â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    total_patients = (
        db.query(func.count(models.Patient.id))
        .filter(models.Patient.employer_id == employer_id)
        .scalar() or 0
    )

    # â”€â”€ DÃ©biteurs (actes EN_ATTENTE) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    debtors_raw = (
        db.query(
            models.Patient.id,
            models.Patient.nom,
            models.Patient.prenom,
            models.Patient.telephone,
            func.sum(models.Acte.montant).label("total_due"),
        )
        .join(models.Acte, models.Acte.patient_id == models.Patient.id)
        .filter(
            models.Patient.employer_id == employer_id,
            models.Acte.statut_paiement == models.PaiementStatut.EN_ATTENTE,
        )
        .group_by(models.Patient.id)
        .having(func.sum(models.Acte.montant) > 0)
        .order_by(func.sum(models.Acte.montant).desc())
        .limit(20)
        .all()
    )

    debtors = [
        {
            "id": r.id,
            "name": f"{r.prenom} {r.nom}",
            "amount": round(r.total_due, 2),
            "phone": r.telephone,
        }
        for r in debtors_raw
    ]

    total_debt = round(sum(d["amount"] for d in debtors), 2)

    user = db.query(models.User).filter(models.User.id == employer_id).first()
    is_superadmin = user and user.email.lower() == "benmoussa.achraf@gmail.com"

    if role == "SECRETAIRE":
        finance_data = {
            "today_revenue": 0.0,
            "month_revenue": 0.0,
            "month_variation": 0.0,
            "appointments_count": len(appointments),
            "weekly_revenue": [{"date": str(today - timedelta(days=6 - i)), "amount": 0.0} for i in range(7)],
            "total_patients": total_patients,
            "total_debt": 0.0,
        }
        debtors_data = []
    else:
        finance_data = {
            "today_revenue": round(today_revenue, 2),
            "month_revenue": round(month_revenue, 2),
            "month_variation": month_variation,
            "appointments_count": len(appointments),
            "weekly_revenue": weekly_revenue,
            "total_patients": total_patients,
            "total_debt": total_debt,
        }
        debtors_data = debtors

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "role": role,
        "is_superadmin": is_superadmin,
        "appointments": appointments,
        "finance": finance_data,
        "debtors": debtors_data,
    }


# â”€â”€ MISE Ã€ JOUR STATUT RENDEZ-VOUS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class AppointmentStatusUpdate(BaseModel):
    status: str


@router.patch(
    "/appointments/{appointment_id}/status",
    summary="Mettre Ã  jour le statut d'un rendez-vous depuis le mobile",
)
def update_appointment_status(
    appointment_id: int,
    body: AppointmentStatusUpdate,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    allowed = {"PLANIFIE", "EN_COURS", "TERMINE", "ANNULE"}
    if body.status not in allowed:
        raise HTTPException(status_code=422, detail=f"Statut invalide. Valeurs: {allowed}")

    apt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
    ).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    apt.status = models.AppointmentStatus(body.status)
    db.commit()
    return {"id": appointment_id, "status": body.status}


@router.post("/register-device")
def register_device(
    payload: dict = Body(...),
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    """E5 â€” Enregistre ou met Ã  jour le token FCM d'un appareil mobile."""
    token = payload.get("fcm_token", "").strip()
    platform = payload.get("platform", "android")
    if not token:
        raise HTTPException(status_code=422, detail="fcm_token required")
    existing = db.query(models.DeviceToken).filter(
        models.DeviceToken.fcm_token == token
    ).first()
    if existing:
        existing.employer_id = employer_id
        existing.platform = platform
    else:
        db.add(models.DeviceToken(employer_id=employer_id, fcm_token=token, platform=platform))
    db.commit()
    return {"status": "registered"}


from typing import Optional
from fastapi.responses import FileResponse
from backend.routers.documents import get_accounting_honoraires
from backend.services.generators.report_gen import ReportGenerator

@router.get("/accounting/export-pdf")
def export_mobile_accounting_pdf(
    year: int, month: int,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db)
):
    current_user = db.query(models.User).filter(models.User.id == employer_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    data = get_accounting_honoraires(None, None, year, month, db, current_user)
    report_gen = ReportGenerator()
    filepath = report_gen.generate_accounting_report(
        items=data["items"], 
        total_amount=data["total_amount"], 
        filters={"month": month, "year": year}
    )
    return FileResponse(path=os.path.join(os.getcwd(), filepath), filename=f"Compta_{year}_{month}.pdf")

# -- AGENDA MOBILE (CRUD) ------------------------------------------------------

class MobileAppointmentCreate(BaseModel):
    datetime_start: str
    patient_name: str
    phone: Optional[str] = None
    motif: str
    duration_minutes: int

@router.get('/appointments', summary='Recuperer les RDV sur une periode')
def get_mobile_appointments(
    start_date: str,
    end_date: str,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59)
    apts = db.query(models.Appointment).filter(
        models.Appointment.employer_id == employer_id,
        models.Appointment.datetime_start >= start_dt,
        models.Appointment.datetime_start <= end_dt
    ).all()
    return [{
        'id': a.id,
        'datetime_start': a.datetime_start.isoformat(),
        'patient_name': f'{a.patient.prenom} {a.patient.nom}' if a.patient else a.patient_name,
        'patient_id': a.patient_id,
        'phone': a.patient.telephone if a.patient else None,
        'motif': a.motif,
        'status': a.status.value if a.status else None,
        'duration_minutes': a.duration_minutes
    } for a in apts]

@router.post('/appointments')
def create_mobile_appointment(
    body: MobileAppointmentCreate,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    dt_start = datetime.fromisoformat(body.datetime_start.replace('Z', ''))
    dt_end = dt_start + timedelta(minutes=body.duration_minutes)
    
    new_apt = models.Appointment(
        employer_id=employer_id,
        patient_name=body.patient_name,
        motif=body.motif,
        datetime_start=dt_start,
        datetime_end=dt_end,
        duration_minutes=body.duration_minutes,
        status=models.AppointmentStatus.PLANIFIE
    )
    db.add(new_apt)
    db.commit()
    db.refresh(new_apt)
    return {'id': new_apt.id, 'status': 'created'}

@router.delete('/appointments/{appointment_id}')
def delete_mobile_appointment(
    appointment_id: int,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    apt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id
    ).first()
    if not apt:
        raise HTTPException(status_code=404, detail='Introuvable')
    db.delete(apt)
    db.commit()
    return {'status': 'deleted'}

@router.get('/patients', summary='Liste simplifiée des patients pour le mobile')
def get_mobile_patients(
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    pts = db.query(models.Patient).filter(models.Patient.employer_id == employer_id).all()
    return [{
        'id': p.id,
        'name': f'{p.prenom} {p.nom}'.strip(),
        'phone': p.telephone
    } for p in pts]

class MobilePatientCreate(BaseModel):
    nom: str
    prenom: str
    telephone: str
    sexe: str = "M"

@router.post('/patients', summary='Créer un patient depuis le mobile')
def create_mobile_patient(
    pt: MobilePatientCreate,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db)
):
    new_pt = models.Patient(
        nom=pt.nom,
        prenom=pt.prenom,
        telephone=pt.telephone,
        sexe=pt.sexe,
        employer_id=employer_id
    )
    db.add(new_pt)
    db.commit()
    db.refresh(new_pt)
    return {'id': new_pt.id, 'name': f"{new_pt.prenom} {new_pt.nom}".strip(), 'phone': new_pt.telephone}


import base64

@router.get('/patients/{patient_id}/documents', summary='Liste des documents à signer pour un patient')
def get_mobile_patient_documents(
    patient_id: int,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    pt = db.query(models.Patient).filter(
        models.Patient.id == patient_id,
        models.Patient.employer_id == employer_id
    ).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Patient introuvable")

    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF,
        models.DocumentArchive.document_type == models.DocumentType.DEVIS
    ).order_by(models.DocumentArchive.created_at.desc()).all()

    res = []
    for d in docs:
        cdata = d.clinical_data or {}
        signed = cdata.get("signed", False)
        res.append({
            "id": d.id,
            "filename": d.original_filename or d.filename,
            "document_type": d.document_type.value,
            "created_at": d.created_at.strftime("%d/%m/%Y"),
            "signed": signed,
            "file_path": f"/api/documents/download/{d.id}"
        })
    return res


class SignatureSubmit(BaseModel):
    signature_base64: str

@router.post('/documents/{document_id}/sign', summary='Signer un document électroniquement')
def sign_mobile_document(
    document_id: int,
    body: SignatureSubmit,
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    doc = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.id == document_id,
        models.DocumentArchive.status == models.DocumentStatus.ACTIF
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    pt = db.query(models.Patient).filter(
        models.Patient.id == doc.patient_id,
        models.Patient.employer_id == employer_id
    ).first()
    if not pt:
        raise HTTPException(status_code=403, detail="Non autorisé")

    sig_data = body.signature_base64
    if "," in sig_data:
        sig_data = sig_data.split(",")[1]

    try:
        sig_bytes = base64.b64decode(sig_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Signature invalide")

    sig_dir = "static/uploads/signatures"
    os.makedirs(sig_dir, exist_ok=True)
    sig_filename = f"sig_{uuid.uuid4().hex}.png"
    sig_path = os.path.join(sig_dir, sig_filename)

    with open(sig_path, "wb") as f:
        f.write(sig_bytes)

    cdata = dict(doc.clinical_data or {})
    cdata["signed"] = True
    cdata["signature_path"] = sig_path.replace("\\", "/")
    cdata["signature_date"] = datetime.utcnow().isoformat()
    doc.clinical_data = cdata

    if doc.document_type == models.DocumentType.DEVIS:
        from backend.services.document_factory import doc_factory
        from backend.schemas import DevisData
        try:
            devis_data = DevisData(**cdata)
            new_file_path = doc_factory.create_devis(pt, devis_data, db=db, user_id=employer_id)
            if os.path.exists(doc.file_path) and doc.file_path != new_file_path:
                try:
                    os.remove(doc.file_path)
                except Exception:
                    pass
            doc.file_path = new_file_path
        except Exception as e:
            import logging
            logger = logging.getLogger("uvicorn")
            logger.error(f"Erreur lors de la régénération du devis : {e}")
            raise HTTPException(status_code=500, detail=f"Erreur de régénération PDF : {e}")

    db.commit()
    return {"status": "success", "signed": True}


