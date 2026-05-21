"""
Routes PWA Mobile — LAN-first, zéro cloud.
Aucune donnée ne sort du réseau local du cabinet.
"""
import uuid
import socket
import os
from datetime import datetime, date, timedelta, time as dt_time, timezone
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import func, extract
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from jose import jwt, JWTError

from backend import models, database
from backend.security import SECRET_KEY, ALGORITHM

router = APIRouter(tags=["Mobile ZKA"])


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _create_mobile_jwt(employer_id: int) -> str:
    """JWT mobile à 24h — type=mobile pour isolation des routes régulières."""
    payload = {
        "sub": str(employer_id),
        "type": "mobile",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_mobile_employer_id(authorization: str = Header(...)) -> int:
    """Dépendance : valide le JWT mobile et retourne l'employer_id."""
    err = HTTPException(status_code=401, detail="Token mobile invalide ou expiré.")
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


def get_lan_base_url() -> str:
    """
    Retourne l'URL LAN du serveur.
    FRONTEND_URL override explicite si non-localhost.
    Sinon, auto-détection IP LAN via socket UDP.
    """
    configured = os.getenv("FRONTEND_URL", "").rstrip("/")
    if configured and "localhost" not in configured and "127.0.0.1" not in configured:
        return configured
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        port = os.getenv("PORT", "8000")
        return f"http://{lan_ip}:{port}"
    except Exception:
        return configured or "http://localhost:8000"


# ── PING ──────────────────────────────────────────────────────────────────────

@router.get("/ping", summary="Vérification de connectivité LAN")
def ping():
    return {"status": "ok", "mode": "lan"}


# ── CLAIM TOKEN ───────────────────────────────────────────────────────────────

class ClaimTokenRequest(BaseModel):
    token: str


@router.post(
    "/claim-token",
    summary="Échanger un token éphémère QR contre un JWT mobile",
    description="Token à usage unique (UUID 5 min). Retourne publicId, masterKey et un JWT mobile 24h.",
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
        raise HTTPException(status_code=404, detail="Token invalide, expiré ou déjà utilisé.")

    record.used_at = datetime.utcnow()
    db.commit()

    return {
        "publicId": record.public_id,
        "masterKey": record.master_key,
        "access_token": _create_mobile_jwt(record.employer_id),
    }


# ── SNAPSHOT LAN-FIRST ────────────────────────────────────────────────────────

@router.get(
    "/snapshot",
    summary="Snapshot temps réel du cabinet — LAN uniquement",
    description="Retourne agenda du jour, KPIs financiers et liste rouge. Données 100% locales.",
)
def get_mobile_snapshot(
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    today = date.today()
    day_start = datetime.combine(today, dt_time.min)
    day_end = datetime.combine(today, dt_time.max)

    # ── Agenda du jour ────────────────────────────────────────────────────────
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

    # ── Recettes du jour ──────────────────────────────────────────────────────
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

    # ── Recettes du mois courant ──────────────────────────────────────────────
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

    # ── Variation mois précédent ──────────────────────────────────────────────
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

    # ── Recettes 7 derniers jours ─────────────────────────────────────────────
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

    # ── Nombre total patients ─────────────────────────────────────────────────
    total_patients = (
        db.query(func.count(models.Patient.id))
        .filter(models.Patient.employer_id == employer_id)
        .scalar() or 0
    )

    # ── Débiteurs (actes EN_ATTENTE) ──────────────────────────────────────────
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

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "appointments": appointments,
        "finance": {
            "today_revenue": round(today_revenue, 2),
            "month_revenue": round(month_revenue, 2),
            "month_variation": month_variation,
            "appointments_count": len(appointments),
            "weekly_revenue": weekly_revenue,
            "total_patients": total_patients,
            "total_debt": total_debt,
        },
        "debtors": debtors,
    }


# ── MISE À JOUR STATUT RENDEZ-VOUS ────────────────────────────────────────────

class AppointmentStatusUpdate(BaseModel):
    status: str


@router.patch(
    "/appointments/{appointment_id}/status",
    summary="Mettre à jour le statut d'un rendez-vous depuis le mobile",
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
