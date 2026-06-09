from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from backend import models, database
from backend.routers.auth import require_permission

router = APIRouter()

class LabJobCreate(BaseModel):
    patient_id: int
    act_id: int
    lab_id: Optional[int] = None
    material: str
    shade: Optional[str] = None
    type: str
    tooth_number: Optional[str] = None
    notes: Optional[str] = None
    deadline: str
    is_remake: bool = False


@router.get("/")
def get_lab_jobs(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    jobs = db.query(models.LabJob).all()
    result = []
    for job in jobs:
        result.append({
            "id": job.id,
            "patient_id": job.patient_id,
            "act_id": job.act_id,
            "lab_id": job.lab_id,
            "material": job.material,
            "shade": job.shade,
            "type": job.type,
            "tooth_number": job.tooth_number,
            "notes": job.notes,
            "deadline": job.deadline.isoformat() if job.deadline else None,
            "status": job.status.value if job.status else None,
            "is_remake": job.is_remake,
            "is_late": job.is_late
        })
    return result

@router.patch("/{job_id}")
def update_lab_job(job_id: int, req: Dict[str, Any], db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    job = db.query(models.LabJob).filter(models.LabJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="LabJob not found")
    
    if "status" in req:
        # Assurez-vous de gérer la chaîne enum correctement si nécessaire, 
        # mais SQLAlchemy le cast souvent automatiquement ou nécessite le membre enum.
        job.status = req["status"]
    
    db.commit()
    db.refresh(job)
    return {
        "id": job.id,
        "status": job.status.value if hasattr(job.status, "value") else job.status
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_lab_job(req: LabJobCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    new_job = models.LabJob(
        patient_id=req.patient_id,
        act_id=req.act_id,
        lab_id=req.lab_id,
        material=req.material,
        shade=req.shade,
        type=req.type,
        tooth_number=req.tooth_number,
        notes=req.notes,
        deadline=datetime.fromisoformat(req.deadline.replace('Z', '+00:00')),
        status=models.LabJobStatus.PRESCRIPTION,
        is_remake=req.is_remake
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return {
        "id": new_job.id,
        "status": new_job.status.value
    }
