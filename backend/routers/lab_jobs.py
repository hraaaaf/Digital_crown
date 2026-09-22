from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from backend import models, database
from backend.routers.auth import require_permission
from backend.utils.access_control import assert_patient_access

router = APIRouter()

class LabCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    notes: Optional[str] = None


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


@router.get("/labs")
def get_labs(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    labs = (
        db.query(models.Lab)
        .filter(models.Lab.employer_id == employer_id)
        .order_by(models.Lab.name.asc())
        .all()
    )
    return [
        {"id": lab.id, "name": lab.name, "phone": lab.phone, "notes": lab.notes}
        for lab in labs
    ]


@router.post("/labs", status_code=status.HTTP_201_CREATED)
def create_lab(
    req: LabCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Nom du laboratoire requis")
    employer_id = current_user.get_employer_id()
    existing = (
        db.query(models.Lab)
        .filter(models.Lab.employer_id == employer_id, models.Lab.name.ilike(name))
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Laboratoire déjà enregistré")
    lab = models.Lab(
        employer_id=employer_id,
        name=name,
        phone=req.phone.strip() if req.phone else None,
        notes=req.notes.strip() if req.notes else None,
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return {"id": lab.id, "name": lab.name, "phone": lab.phone, "notes": lab.notes}


@router.delete("/labs/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab(
    lab_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    employer_id = current_user.get_employer_id()
    lab = (
        db.query(models.Lab)
        .filter(models.Lab.id == lab_id, models.Lab.employer_id == employer_id)
        .first()
    )
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratoire introuvable")
    in_use = db.query(models.LabJob).filter(models.LabJob.lab_id == lab.id).first()
    if in_use:
        raise HTTPException(status_code=409, detail="Laboratoire utilisé par un travail")
    db.delete(lab)
    db.commit()


@router.get("/")
def get_lab_jobs(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    employer_id = current_user.get_employer_id()
    jobs = (
        db.query(models.LabJob)
        .join(models.Patient, models.LabJob.patient_id == models.Patient.id)
        .filter(models.Patient.employer_id == employer_id)
        .all()
    )
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
    assert_patient_access(job.patient_id, current_user, db)
    
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
    assert_patient_access(req.patient_id, current_user, db)
    employer_id = current_user.get_employer_id()
    if req.lab_id is not None:
        lab = db.query(models.Lab).filter(
            models.Lab.id == req.lab_id,
            models.Lab.employer_id == employer_id,
        ).first()
        if not lab:
            raise HTTPException(status_code=422, detail="Laboratoire invalide pour ce cabinet")

    act = db.query(models.Acte).filter(
        models.Acte.id == req.act_id,
        models.Acte.patient_id == req.patient_id,
    ).first()
    if not act:
        raise HTTPException(status_code=422, detail="Acte incompatible avec ce patient")

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
