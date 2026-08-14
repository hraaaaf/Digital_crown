"""
Routes PWA Mobile — LAN-first, zéro cloud.
Aucune donnée ne sort du réseau local du cabinet.
"""
import uuid
import socket
import os
import re
from typing import Optional
from datetime import datetime, date, timedelta, time as dt_time, timezone
from fastapi import APIRouter, Depends, HTTPException, Header, Body, BackgroundTasks
from sqlalchemy import func, extract
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from jose import jwt, JWTError

from backend import models, database
from backend.config import settings
from backend.security import SECRET_KEY, ALGORITHM
from backend.services.zka_crypto import encrypt_payload, decrypt_payload

router = APIRouter(tags=["Mobile ZKA"])


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _create_mobile_jwt(employer_id: int, role: str) -> str:
    """JWT mobile court avec JTI obligatoire pour permettre une révocation effective."""
    payload = {
        "sub": str(employer_id),
        "type": "mobile",
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.MOBILE_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_mobile_employer_id(
    authorization: str = Header(...), 
    db: Session = Depends(database.get_db)
) -> int:
    """Dépendance : valide le JWT mobile, vérifie la révocation et retourne l'employer_id."""
    err = HTTPException(status_code=401, detail="Token mobile invalide, expiré ou révoqué.")
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise err
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "mobile":
            raise err

        jti = payload.get("jti")
        if not jti:
            raise err
        from backend.security import token_blacklist
        if token_blacklist.is_revoked(jti, db):
            raise err

        user_id = int(payload["sub"])
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user or not user.is_active:
            raise err

        return user_id
    except (JWTError, ValueError, KeyError):
        raise err

def get_mobile_role(
    authorization: str = Header(...),
    db: Session = Depends(database.get_db)
) -> str:
    """Dépendance : valide le JWT mobile, vérifie la révocation et retourne le role.

    FAIL-CLOSED (S5) : tout token révoqué/invalide/sans claim de rôle est ramené au
    MOINDRE privilège (SECRETAIRE), jamais à DENTISTE — pour ne jamais exposer les
    données financières par défaut. (La révocation est de toute façon déjà bloquée
    en amont par get_mobile_employer_id qui lève 401.)
    """
    LEAST_PRIVILEGE = "SECRETAIRE"
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() == "bearer":
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "mobile":
                return LEAST_PRIVILEGE
            jti = payload.get("jti")
            if not jti:
                return LEAST_PRIVILEGE
            from backend.security import token_blacklist
            if token_blacklist.is_revoked(jti, db):
                return LEAST_PRIVILEGE
            return payload.get("role", LEAST_PRIVILEGE)
    except Exception:
        pass
    return LEAST_PRIVILEGE


def _detect_lan_ip() -> str:
    """Auto-détecte l'IP LAN courante via socket (robuste aux changements DHCP)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        return lan_ip
    except Exception:
        return "127.0.0.1"


def get_lan_base_url() -> str:
    """URL LAN du backend — auto-détectée, toujours HTTP."""
    port = os.getenv("PORT", "8005")
    return f"http://{_detect_lan_ip()}:{port}"


def get_lan_frontend_url() -> str:
    """URL LAN du frontend (Vite :5173) — auto-détectée."""
    return f"http://{_detect_lan_ip()}:5173"


def resolve_frontend_url(configured: str | None) -> str:
    """
    Résout l'URL du frontend. Si la valeur configurée est vide ou pointe vers
    localhost / une IP LAN privée (valeur qui se périme au gré du DHCP), on
    auto-détecte l'IP LAN courante. Une URL non-locale (vrai domaine) est respectée.
    """
    configured = (configured or "").rstrip("/")
    is_local_or_lan = re.search(
        r"://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)(:|/|$)",
        configured,
    )
    if not configured or is_local_or_lan:
        return get_lan_frontend_url()
    return configured


# ── MAPPING STATUT RDV ────────────────────────────────────────────────────────
# Le mobile utilise un vocabulaire simplifié à 4 états ; le métier en a 5.
_MOBILE_TO_BACKEND_STATUS = {
    "PLANIFIE": models.AppointmentStatus.PREVU,
    "EN_COURS": models.AppointmentStatus.EN_FAUTEUIL,
    "TERMINE": models.AppointmentStatus.TERMINE,
    "ANNULE": models.AppointmentStatus.ANNULE,
}
_BACKEND_TO_MOBILE_STATUS = {
    models.AppointmentStatus.PREVU: "PLANIFIE",
    models.AppointmentStatus.EN_SALLE_ATTENTE: "PLANIFIE",
    models.AppointmentStatus.EN_FAUTEUIL: "EN_COURS",
    models.AppointmentStatus.TERMINE: "TERMINE",
    models.AppointmentStatus.ANNULE: "ANNULE",
}


def _to_mobile_status(status) -> Optional[str]:
    """Convertit un statut métier en vocabulaire mobile (défaut: PLANIFIE)."""
    if status is None:
        return None
    return _BACKEND_TO_MOBILE_STATUS.get(status, "PLANIFIE")


# ── PING ──────────────────────────────────────────────────────────────────────

@router.get("/ping", summary="Vérification de connectivité LAN")
def ping():
    return {"status": "ok", "mode": "lan"}


@router.get("/ca-cert", summary="Profil iOS (.mobileconfig) pour installation HTTPS sans friction")
def get_ca_cert():
    """
    Sert un profil Apple .mobileconfig contenant le certificat CA mkcert.
    Quand Safari ouvre ce fichier, iOS propose directement l'installation — aucune manipulation manuelle.
    Accessible sans authentification (clé publique uniquement).
    """
    import subprocess
    import pathlib
    import base64
    import uuid
    from fastapi.responses import Response as FastAPIResponse

    try:
        ca_root = subprocess.check_output(["mkcert", "-CAROOT"], text=True).strip()
        ca_file = pathlib.Path(ca_root) / "rootCA.pem"
    except Exception:
        ca_file = None

    if not ca_file or not ca_file.exists():
        raise HTTPException(status_code=404, detail="Certificat CA non trouvé. Lancez scripts/setup-https.ps1 d'abord.")

    # Lire le PEM et extraire les bytes DER (entre -----BEGIN/END CERTIFICATE-----)
    pem_text = ca_file.read_text()
    b64_lines = [l for l in pem_text.splitlines()
                 if l and not l.startswith("-----")]
    cert_b64 = "".join(b64_lines)

    profile_uuid = str(uuid.uuid4()).upper()
    payload_uuid = str(uuid.uuid4()).upper()

    mobileconfig = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <dict>
            <key>PayloadCertificateFileName</key>
            <string>DigitalCrown-CA.crt</string>
            <key>PayloadContent</key>
            <data>{cert_b64}</data>
            <key>PayloadDescription</key>
            <string>Autorise la connexion sécurisée HTTPS au cabinet sur le réseau local.</string>
            <key>PayloadDisplayName</key>
            <string>Digital Crown — Certificat Cabinet</string>
            <key>PayloadIdentifier</key>
            <string>com.digitalcrown.ca.cert</string>
            <key>PayloadType</key>
            <string>com.apple.security.root</string>
            <key>PayloadUUID</key>
            <string>{payload_uuid}</string>
            <key>PayloadVersion</key>
            <integer>1</integer>
        </dict>
    </array>
    <key>PayloadDescription</key>
    <string>Active la connexion chiffrée entre cet iPhone et le logiciel Digital Crown de votre cabinet dentaire.</string>
    <key>PayloadDisplayName</key>
    <string>Digital Crown — Sécurité Cabinet</string>
    <key>PayloadIdentifier</key>
    <string>com.digitalcrown.profile</string>
    <key>PayloadOrganization</key>
    <string>Digital Crown</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadUUID</key>
    <string>{profile_uuid}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>"""

    return FastAPIResponse(
        content=mobileconfig.encode("utf-8"),
        media_type="application/x-apple-aspen-config",
        headers={"Content-Disposition": 'attachment; filename="DigitalCrown-Securite.mobileconfig"'},
    )


# ── CLAIM TOKEN ────────────────────────────────────────────────────────────────

class ClaimTokenRequest(BaseModel):
    token: str
    client_public_key_hex: str = None

@router.post(
    "/claim-token",
    summary="Échanger un token éphémère QR contre un JWT mobile",
    description="Token à usage unique (UUID 5 min). Si client_public_key_hex est fourni, utilise ECDH (secp256r1) pour chiffrer la masterKey.",
)
def claim_pairing_token(
    body: ClaimTokenRequest,
    db: Session = Depends(database.get_db),
):
    now = datetime.utcnow()
    record = (
        db.query(models.ZKAPairingToken)
        .filter(
            models.ZKAPairingToken.token == body.token,
            models.ZKAPairingToken.used_at == None,  # noqa: E711
            models.ZKAPairingToken.expires_at > now,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Token invalide, expiré ou déjà utilisé.")

    # ZKA (S5) : l'appairage sécurisé par ECDH est OBLIGATOIRE.
    # Le token one-shot ne doit être consommé qu'après un handshake complet.
    if not body.client_public_key_hex:
        raise HTTPException(
            status_code=400,
            detail="Appairage sécurisé requis : clé publique client (ECDH) manquante.",
        )

    role = getattr(record, "role", "DENTISTE")
    public_id = record.public_id
    employer_id = record.employer_id
    master_key = record.master_key

    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        client_pub_bytes = bytes.fromhex(body.client_public_key_hex)
        client_public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), client_pub_bytes)

        server_private_key = ec.generate_private_key(ec.SECP256R1())
        server_public_key = server_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )

        shared_key = server_private_key.exchange(ec.ECDH(), client_public_key)

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'zka_mobile_bridge'
        ).derive(shared_key)

        aesgcm = AESGCM(derived_key)
        nonce = os.urandom(12)
        encrypted_master_key = aesgcm.encrypt(nonce, master_key.encode(), None)
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Erreur ECDH: {e}")
        raise HTTPException(status_code=400, detail="Cle publique client invalide.")

    # Consommation atomique : un second claim concurrent ne peut pas gagner.
    claimed_at = datetime.utcnow()
    updated = (
        db.query(models.ZKAPairingToken)
        .filter(
            models.ZKAPairingToken.id == record.id,
            models.ZKAPairingToken.used_at == None,  # noqa: E711
            models.ZKAPairingToken.expires_at > claimed_at,
        )
        .update({models.ZKAPairingToken.used_at: claimed_at}, synchronize_session=False)
    )
    if updated != 1:
        db.rollback()
        raise HTTPException(status_code=409, detail="Token déjà utilisé ou expiré pendant l'appairage.")
    db.commit()

    return {
        "publicId": public_id,
        "role": role,
        "access_token": _create_mobile_jwt(employer_id, role),
        "server_public_key_hex": server_public_key.hex(),
        "encrypted_master_key_hex": (nonce + encrypted_master_key).hex(),
    }


# ── SNAPSHOT LAN-FIRST ────────────────────────────────────────────────────────

@router.get(
    "/snapshot",
    summary="Snapshot temps réel du cabinet — LAN uniquement",
    description="Retourne agenda du jour, KPIs financiers et liste rouge. Données 100% locales.",
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
            "patient_id": a.patient_id,
            "time": a.datetime_start.strftime("%H:%M"),
            "patient_name": (
                f"{a.patient.prenom} {a.patient.nom}"
                if a.patient else (a.patient_name or "Patient inconnu")
            ),
            "phone": a.patient.telephone if a.patient else None,
            "motif": a.motif or "Consultation",
            "status": _to_mobile_status(a.status),
            "duration_minutes": a.duration_minutes,
        }
        for a in apts
    ]

    # ──────────────────────────────────────────────────────────────────────────────────────────────────
    from backend.services.accounting_service import accounting_service
    kpis = accounting_service.get_finance_kpis(db, employer_id, today)

    # Nombre total patients 
    total_patients = (
        db.query(func.count(models.Patient.id))
        .filter(models.Patient.employer_id == employer_id)
        .scalar() or 0
    )

    from backend.config import settings as app_settings
    _superadmin_email = app_settings.SUPERADMIN_EMAIL.lower().strip()
    user = db.query(models.User).filter(models.User.id == employer_id).first()
    is_superadmin = bool(_superadmin_email and user and user.email.lower() == _superadmin_email)

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
            "today_revenue": kpis["today_revenue"],
            "month_revenue": kpis["month_revenue"],
            "month_variation": kpis["month_variation"],
            "appointments_count": len(appointments),
            "weekly_revenue": kpis["weekly_revenue"],
            "total_patients": total_patients,
            "total_debt": kpis["total_debt"],
        }
        debtors_data = kpis["debtors"]

    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "role": role,
        "is_superadmin": is_superadmin,
        "appointments": appointments,
        "finance": finance_data,
        "debtors": debtors_data,
    }
    
    return encrypt_payload(data)


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
    backend_status = _MOBILE_TO_BACKEND_STATUS.get(body.status)
    if backend_status is None:
        valeurs = ", ".join(_MOBILE_TO_BACKEND_STATUS.keys())
        raise HTTPException(status_code=422, detail=f"Statut invalide. Valeurs: {valeurs}")

    apt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id,
        models.Appointment.employer_id == employer_id,
    ).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Rendez-vous introuvable.")

    apt.status = backend_status
    db.commit()
    return {"id": appointment_id, "status": body.status}


@router.post("/register-device")
def register_device(
    payload: dict = Body(...),
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    """E5 — Enregistre ou met à jour le token FCM d'un appareil mobile."""
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


from fastapi.responses import FileResponse
from backend.routers.accounting import get_accounting_honoraires
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

# ── LISTE DES PRATICIENS (vue secrétaire) ──────────────────────────────────────

@router.get("/dentists", summary="Liste des praticiens du cabinet — vue secrétaire mobile")
def get_mobile_dentists(
    employer_id: int = Depends(get_mobile_employer_id),
    db: Session = Depends(database.get_db),
):
    today = date.today()
    day_start = datetime.combine(today, dt_time.min)
    day_end = datetime.combine(today, dt_time.max)

    owner = db.query(models.User).filter(models.User.id == employer_id).first()
    sub_dentists = (
        db.query(models.User)
        .filter(
            models.User.employer_id == employer_id,
            models.User.role == models.UserRole.DENTISTE,
            models.User.is_active == True,  # noqa: E712
        )
        .all()
    )
    all_dentists = ([owner] if owner else []) + list(sub_dentists)

    today_count = (
        db.query(func.count(models.Appointment.id))
        .filter(
            models.Appointment.employer_id == employer_id,
            models.Appointment.datetime_start >= day_start,
            models.Appointment.datetime_start <= day_end,
            models.Appointment.status != models.AppointmentStatus.ANNULE,
        )
        .scalar() or 0
    )

    result = [
        {
            "id": d.id,
            "name": d.nom_complet or d.email,
            "email": d.email,
            "today_appointments": today_count if i == 0 else 0,
        }
        for i, d in enumerate(all_dentists)
    ]
    return {"dentists": result}


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
    data = [{
        'id': a.id,
        'datetime_start': a.datetime_start.isoformat(),
        'patient_name': f'{a.patient.prenom} {a.patient.nom}' if a.patient else a.patient_name,
        'patient_id': a.patient_id,
        'phone': a.patient.telephone if a.patient else None,
        'motif': a.motif,
        'status': _to_mobile_status(a.status),
        'duration_minutes': a.duration_minutes
    } for a in apts]
    return encrypt_payload({"data": data})

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
        status=models.AppointmentStatus.PREVU
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
    data = [{
        'id': p.id,
        'name': f'{p.prenom} {p.nom}'.strip(),
        'phone': p.telephone
    } for p in pts]
    return encrypt_payload({"data": data})

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
    return encrypt_payload({"data": res})


class SignatureSubmit(BaseModel):
    signature_base64: str

def background_regenerate_pdf(document_id: int, pt_id: int, cdata: dict, employer_id: int, old_file_path: str):
    from backend.database import SessionLocal
    db_bg = SessionLocal()
    try:
        from backend.models import DocumentArchive, Patient
        from backend.services.document_factory import doc_factory
        from backend.schemas import DevisData
        import os
        
        doc = db_bg.query(DocumentArchive).filter(DocumentArchive.id == document_id).first()
        pt = db_bg.query(Patient).filter(Patient.id == pt_id).first()
        if not doc or not pt:
            return
            
        devis_data = DevisData(**cdata)
        new_file_path = doc_factory.create_devis(pt, devis_data, db=db_bg, user_id=employer_id)
        
        if old_file_path and os.path.exists(old_file_path) and old_file_path != new_file_path:
            try:
                os.remove(old_file_path)
            except Exception:
                pass
                
        doc.file_path = new_file_path
        db_bg.commit()
    except Exception as e:
        import logging
        logger = logging.getLogger("uvicorn")
        logger.error(f"Erreur background_regenerate_pdf : {e}")
    finally:
        db_bg.close()

@router.post('/documents/{document_id}/sign', summary='Signer un document électroniquement')
def sign_mobile_document(
    document_id: int,
    body: SignatureSubmit,
    background_tasks: BackgroundTasks,
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
    
    old_file_path = doc.file_path

    if doc.document_type == models.DocumentType.DEVIS:
        background_tasks.add_task(
            background_regenerate_pdf,
            document_id=doc.id,
            pt_id=pt.id,
            cdata=cdata,
            employer_id=employer_id,
            old_file_path=old_file_path
        )

    db.commit()
    return {"status": "success", "signed": True}
