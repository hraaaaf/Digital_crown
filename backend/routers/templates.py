from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from backend import models, schemas, database
from backend.routers.auth import get_current_user

router = APIRouter(tags=["Templates"])

@router.get("/")
def list_system_templates(type: Optional[str] = None, is_system: Optional[bool] = True, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.DocumentTemplate)
    if is_system is True:
        query = query.filter(models.DocumentTemplate.is_system == True)
    else:
        from sqlalchemy import or_
        employer_id = current_user.get_employer_id()
        team_users = db.query(models.User.id).filter(models.User.employer_id == employer_id).all()
        team_ids = [r[0] for r in team_users] + [employer_id]
        query = query.filter(or_(
            models.DocumentTemplate.is_system == True,
            models.DocumentTemplate.user_id.in_(team_ids)
        ))
        if is_system is False:
            query = query.filter(models.DocumentTemplate.is_system == False)
            
    if type: query = query.filter(models.DocumentTemplate.type == type)
    templates = query.all()
    return [{"id": t.id, "type": t.type.value if hasattr(t.type, 'value') else t.type, "style_key": t.style_key, "name": t.name, "is_default": t.is_default, "description": t.description} for t in templates]

@router.get("/{template_id}", response_model=schemas.DocumentTemplateOut)
def get_template(template_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if not template: raise HTTPException(status_code=404, detail="Template non trouvé")
    if not template.is_system:
        employer_id = current_user.get_employer_id()
        team_users = db.query(models.User.id).filter(models.User.employer_id == employer_id).all()
        team_ids = [r[0] for r in team_users] + [employer_id]
        if template.user_id not in team_ids:
            raise HTTPException(status_code=403, detail="Accès refusé")
    return template

@router.post("/", response_model=schemas.DocumentTemplateOut)
def create_template(template: schemas.DocumentTemplateCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    if template.is_system and current_user.email.lower() != "benmoussa.achraf@gmail.com":
        raise HTTPException(status_code=403, detail="SuperAdmin only")
    db_template = models.DocumentTemplate(**template.model_dump(exclude={"design_config"}), design_config=template.design_config.model_dump() if template.design_config else {}, user_id=current_user.id if not template.is_system else None)
    if template.is_default:
        db.query(models.DocumentTemplate).filter(models.DocumentTemplate.type == template.type, models.DocumentTemplate.user_id == (current_user.id if not template.is_system else None)).update({"is_default": False})
    db.add(db_template); db.commit(); db.refresh(db_template)
    return db_template

@router.post("/{template_id}/set-default")
def set_default_template(template_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if not template: raise HTTPException(status_code=404, detail="Template non trouvé")
    if template.is_system: raise HTTPException(status_code=403, detail="Impossible de modifier un template système")
    
    employer_id = current_user.get_employer_id()
    team_users = db.query(models.User.id).filter(models.User.employer_id == employer_id).all()
    team_ids = [r[0] for r in team_users] + [employer_id]
    if template.user_id not in team_ids:
        raise HTTPException(status_code=403, detail="Accès refusé")
    db.query(models.DocumentTemplate).filter(models.DocumentTemplate.type == template.type, models.DocumentTemplate.user_id == template.user_id).update({"is_default": False})
    template.is_default = True
    db.commit()
    return {"message": "Template défini par défaut"}

@router.delete("/{template_id}")
def delete_template(template_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if not template: raise HTTPException(status_code=404, detail="Template non trouvé")
    if template.is_system: raise HTTPException(status_code=403, detail="Impossible de supprimer un template système")
    
    employer_id = current_user.get_employer_id()
    team_users = db.query(models.User.id).filter(models.User.employer_id == employer_id).all()
    team_ids = [r[0] for r in team_users] + [employer_id]
    if template.user_id not in team_ids:
        raise HTTPException(status_code=403, detail="Accès refusé")
    db.delete(template); db.commit()
    return {"message": "Template supprimé"}
