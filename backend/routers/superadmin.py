from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

from backend import models, database
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/superadmin", tags=["SuperAdmin"])

def verify_superadmin(current_user: models.User = Depends(get_current_user)):
    if current_user.email.lower() != "benmoussa.achraf@gmail.com":
        raise HTTPException(status_code=403, detail="Accès refusé. Réservé au SuperAdmin.")
    return current_user

@router.get("/clients")
def get_clients(db: Session = Depends(database.get_db), admin: models.User = Depends(verify_superadmin)):
    clients = db.query(models.User).filter(
        models.User.role.in_([models.UserRole.ADMIN, models.UserRole.DENTISTE]),
        models.User.employer_id == None
    ).all()
    
    result = []
    for c in clients:
        # Calculate total patients
        total_patients = db.query(models.Patient).filter(models.Patient.employer_id == c.id).count()
        result.append({
            "id": c.id,
            "nom_complet": c.nom_complet or "N/A",
            "email": c.email,
            "telephone": c.telephone_mobile or c.telephone_fixe or "N/A",
            "cabinet_name": c.specialites or "Cabinet Dentaire",
            "total_patients": total_patients,
            "is_licensed": c.is_licensed,
            "license_expires_at": c.license_expires_at.isoformat() if c.license_expires_at else None,
            "created_at": datetime.utcnow().isoformat() # Placeholder since we don't have created_at on user
        })
    return result

@router.post("/clients/{user_id}/grant-license")
def grant_license(
    user_id: int, 
    action: str = Query(...), 
    db: Session = Depends(database.get_db), 
    admin: models.User = Depends(verify_superadmin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    
    now = datetime.utcnow()
    current_expiry = user.license_expires_at if user.license_expires_at and user.license_expires_at > now else now
    
    if action == "1m":
        user.license_expires_at = current_expiry + timedelta(days=30)
        user.is_licensed = True
    elif action == "3m":
        user.license_expires_at = current_expiry + timedelta(days=90)
        user.is_licensed = True
    elif action == "6m":
        user.license_expires_at = current_expiry + timedelta(days=180)
        user.is_licensed = True
    elif action == "1y":
        user.license_expires_at = current_expiry + timedelta(days=365)
        user.is_licensed = True
    elif action == "revoke":
        user.license_expires_at = now - timedelta(days=1)
        user.is_licensed = False
    else:
        raise HTTPException(status_code=400, detail="Action non valide.")
        
    db.commit()
    return {"status": "success", "license_expires_at": user.license_expires_at}
