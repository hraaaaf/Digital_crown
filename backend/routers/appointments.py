from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Appointments"])

@router.get("/", response_model=List[schemas.AppointmentOut])
def get_appointments(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_employer_id = current_user.get_employer_id()
    query = db.query(models.Appointment).filter(models.Appointment.employer_id == user_employer_id)
    if start_date:
        query = query.filter(models.Appointment.datetime_start >= datetime.fromisoformat(start_date.replace("Z", "+00:00")))
    if end_date:
        query = query.filter(models.Appointment.datetime_start <= datetime.fromisoformat(end_date.replace("Z", "+00:00")))
    return query.order_by(models.Appointment.datetime_start.asc()).all()

@router.post("/", response_model=schemas.AppointmentOut)
def create_appointment(
    appt: schemas.AppointmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    if appt.patient_id:
        assert_patient_access(appt.patient_id, current_user, db)
        
    appt_data = appt.model_dump()
    appt_data['employer_id'] = current_user.get_employer_id()
    db_appt = models.Appointment(**appt_data)
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

@router.put("/{id}", response_model=schemas.AppointmentOut)
def update_appointment(
    id: int,
    appt_update: schemas.AppointmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_employer_id = current_user.get_employer_id()
    db_appt = db.query(models.Appointment).filter(
        models.Appointment.id == id,
        models.Appointment.employer_id == user_employer_id
    ).first()
    if not db_appt: raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    
    update_data = appt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_appt, key, value)
        
    db.commit()
    db.refresh(db_appt)
    return db_appt

@router.delete("/{id}")
def delete_appointment(id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    user_employer_id = current_user.get_employer_id()
    db_appt = db.query(models.Appointment).filter(
        models.Appointment.id == id,
        models.Appointment.employer_id == user_employer_id
    ).first()
    if not db_appt: raise HTTPException(status_code=404, detail="Rendez-vous introuvable")
    db.delete(db_appt)
    db.commit()
    return {"status": "success"}

@router.post("/bulk", response_model=List[schemas.AppointmentOut])
def create_bulk_appointments(
    payload: schemas.AppointmentBulkCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    created_appts = []
    user_employer_id = current_user.get_employer_id()
    for item in payload.appointments:
        if item.patient_id:
            assert_patient_access(item.patient_id, current_user, db)
            
        db_appt = models.Appointment(
            patient_name=item.patient_name,
            patient_id=item.patient_id,
            datetime_start=item.datetime_start,
            duration_minutes=item.duration_minutes,
            notes=item.notes,
            status=item.status,
            employer_id=user_employer_id
        )
        db.add(db_appt)
        created_appts.append(db_appt)
    
    db.commit()
    for appt in created_appts:
        db.refresh(appt)
        
    return created_appts
