from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models, database
from backend.routers.auth import get_current_user

router = APIRouter(tags=["Statistiques"])

@router.get("/dashboard")
def get_document_stats(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    user_employer_id = current_user.get_employer_id()
    total_docs = db.query(models.DocumentArchive).join(models.Patient).filter(models.Patient.employer_id == user_employer_id).count()
    total_size = db.query(func.sum(models.DocumentArchive.file_size)).join(models.Patient).filter(models.Patient.employer_id == user_employer_id).scalar() or 0
    by_type = db.query(models.DocumentArchive.document_type, func.count(models.DocumentArchive.id)).join(models.Patient).filter(models.Patient.employer_id == user_employer_id).group_by(models.DocumentArchive.document_type).all()
    return {"total_documents": total_docs, "total_size_mb": round(total_size / (1024*1024), 2), "by_type": {t.value: c for t, c in by_type}}
