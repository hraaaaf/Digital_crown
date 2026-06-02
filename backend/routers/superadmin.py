import os
from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from backend import models, database
from backend.routers.auth import get_current_user
from backend.schemas.superadmin import ClientOut, ClientBaseStats, LicenseHistoryOut, UpdateClientNotes, SendRenewalEmailRequest
from backend.main import invalidate_license_cache
from backend.services.license_service import LicenseService
from backend.services.notification_service import notification_service

router = APIRouter(tags=["SuperAdmin"])

_SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "").lower().strip()

def verify_superadmin(current_user: models.User = Depends(get_current_user)):
    if not _SUPERADMIN_EMAIL or current_user.email.lower() != _SUPERADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Accès refusé. Réservé au SuperAdmin.")
    return current_user

def add_license_history(db: Session, user_id: int, admin_id: int, action: str, duration: int = None):
    history = models.LicenseHistory(
        user_id=user_id,
        admin_id=admin_id,
        action=action,
        duration=duration
    )
    db.add(history)

@router.get("/clients", response_model=List[ClientOut])
def get_clients(db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    clients = db.query(models.User).filter(
        models.User.role.in_([models.UserRole.ADMIN, models.UserRole.DENTISTE]),
        models.User.employer_id == None
    ).all()
    
    result = []
    for c in clients:
        total_patients = db.query(models.Patient).filter(models.Patient.employer_id == c.id).count()
        
        # Calculate AI stats (panoramique, cephalo) for this client's patients
        patients_subquery = db.query(models.Patient.id).filter(models.Patient.employer_id == c.id).subquery()
        
        total_pano = db.query(models.PanoramicAnalysis).filter(models.PanoramicAnalysis.patient_id.in_(patients_subquery)).count()
        total_ceph = db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id.in_(patients_subquery)).count()
        
        c_dict = c.__dict__.copy()
        c_dict['stats'] = ClientBaseStats(
            total_patients=total_patients,
            total_ia_panoramique=total_pano,
            total_ia_cephalo=total_ceph
        )
        result.append(c_dict)
    return result

@router.post("/clients/{user_id}/grant-license")
def grant_license(
    user_id: int, 
    background_tasks: BackgroundTasks,
    action: str = Query(...), 
    db: Session = Depends(database.get_db), 
    admin: models.User = Depends(verify_superadmin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    now = datetime.utcnow()
    current_expiry = user.license_expires_at if user.license_expires_at and user.license_expires_at > now else now
    duration = None
    
    if action == "1m":
        duration = 30
    elif action == "3m":
        duration = 90
    elif action == "6m":
        duration = 180
    elif action == "1y":
        duration = 365
    elif action == "revoke":
        user.license_expires_at = now - timedelta(days=1)
        user.is_licensed = False
        add_license_history(db, user_id, admin.id, "revoke")
        db.commit()
        
        invalidate_license_cache(user.email)
        cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
        if cabinet:
            background_tasks.add_task(
                LicenseService().write_license,
                public_id=cabinet.public_id,
                active=False,
                expiration_date=user.license_expires_at
            )
        return {"status": "success", "license_expires_at": user.license_expires_at}
    else:
        raise HTTPException(status_code=400, detail="Action non valide.")
    
    user.license_expires_at = current_expiry + timedelta(days=duration)
    user.is_licensed = True
    add_license_history(db, user_id, admin.id, "grant", duration)
    db.commit()

    invalidate_license_cache(user.email)
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    if cabinet:
        background_tasks.add_task(
            LicenseService().write_license,
            public_id=cabinet.public_id,
            active=True,
            expiration_date=user.license_expires_at
        )

    return {"status": "success", "license_expires_at": user.license_expires_at}

@router.patch("/clients/{user_id}/archive")
def archive_client(user_id: int, db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    user.is_archived = not user.is_archived
    add_license_history(db, user_id, admin.id, "archive" if user.is_archived else "unarchive")
    db.commit()
    invalidate_license_cache(user.email)
    return {"status": "success", "is_archived": user.is_archived}

@router.patch("/clients/{user_id}/suspend")
def suspend_client(user_id: int, db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    user.is_suspended = not user.is_suspended
    add_license_history(db, user_id, admin.id, "suspend" if user.is_suspended else "unsuspend")
    db.commit()
    invalidate_license_cache(user.email)
    return {"status": "success", "is_suspended": user.is_suspended}

@router.patch("/clients/{user_id}/notes")
def update_client_notes(user_id: int, data: UpdateClientNotes, db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    user.internal_notes = data.internal_notes
    db.commit()
    return {"status": "success", "internal_notes": user.internal_notes}

@router.get("/clients/{user_id}/license-history", response_model=List[LicenseHistoryOut])
def get_license_history(user_id: int, db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    history = db.query(models.LicenseHistory).filter(models.LicenseHistory.user_id == user_id).order_by(models.LicenseHistory.timestamp.desc()).all()
    return history

@router.post("/clients/{user_id}/send-renewal-email")
def send_renewal_email(user_id: int, data: SendRenewalEmailRequest, db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    phone = user.telephone_mobile or user.telephone_fixe
    if phone:
        msg = f"Bonjour Dr. {user.nom_complet}, votre licence Digital Crown expire bientôt. {data.message}"
        notification_service.send_whatsapp_via_whatsmate(phone, msg)
        message_status = f"WhatsApp de relance envoyé avec succès à {phone}."
    else:
        message_status = "Aucun numéro de téléphone trouvé pour l'envoi WhatsApp."
        
    add_license_history(db, user_id, admin.id, "renewal_whatsapp_sent")
    db.commit()
    return {"status": "success", "message": message_status}
