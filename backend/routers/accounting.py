from sqlalchemy import func, or_, and_
from typing import Optional, List, Dict
from fastapi.responses import FileResponse
import os
from backend.services.generators.report_gen import ReportGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Accounting & Payments"])

@router.post("/plans", response_model=schemas.InstallmentPlanOut)
def create_installment_plan(plan: schemas.InstallmentPlanCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Crée un nouveau plan de paiement avec ses échéances."""
    assert_patient_access(plan.patient_id, current_user, db)
    new_plan = models.InstallmentPlan(
        patient_id=plan.patient_id,
        title=plan.title,
        total_amount=plan.total_amount
    )
    db.add(new_plan)
    db.flush() # Pour avoir l'ID du plan
    
    for inst in plan.installments:
        new_inst = models.Installment(
            plan_id=new_plan.id,
            label=inst.label,
            amount=inst.amount,
            due_date=inst.due_date,
            status=inst.status,
            notes=inst.notes
        )
        db.add(new_inst)
    
    db.commit()
    db.refresh(new_plan)
    return new_plan

@router.get("/plans/patient/{patient_id}", response_model=List[schemas.InstallmentPlanOut])
def get_patient_plans(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Récupère tous les plans de paiement d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.InstallmentPlan).filter(models.InstallmentPlan.patient_id == patient_id).all()

@router.put("/installments/{installment_id}", response_model=schemas.InstallmentOut)
def update_installment(installment_id: int, updates: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Met à jour une échéance (marquer comme payée, changer date, etc.)."""
    inst = db.query(models.Installment).filter(models.Installment.id == installment_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Échéance introuvable")
    
    assert_patient_access(inst.plan.patient_id, current_user, db)
    
    for key, value in updates.items():
        if hasattr(inst, key):
            if key in ['due_date', 'paid_date'] and value:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            setattr(inst, key, value)
    
    db.commit()
    db.refresh(inst)
    return inst

@router.delete("/plans/{plan_id}")
def delete_installment_plan(plan_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Supprime un plan de paiement complet."""
    plan = db.query(models.InstallmentPlan).filter(models.InstallmentPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan introuvable")
    
    assert_patient_access(plan.patient_id, current_user, db)
    
    db.delete(plan)
    db.commit()
    return {"status": "success", "message": "Plan supprimé"}

@router.get("/frequent-acts", response_model=List[dict])
def get_frequent_acts(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Récupère les actes les plus fréquents du praticien."""
    from backend.services.accounting_service import accounting_service
    return accounting_service.get_frequent_acts(db, current_user.id)

@router.post("/record-act")
def record_act(data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Enregistre manuellement l'usage d'un acte pour l'apprentissage."""
    from backend.services.accounting_service import accounting_service
    accounting_service.record_act_usage(
        db, 
        current_user.id, 
        data.get("name"), 
        float(data.get("price", 0.0)), 
        data.get("category")
    )
    return {"status": "success"}

# --- NEW : PAYMENT TRACKING (Encaissements Réels) ---

@router.post("/payments", response_model=schemas.PaymentOut)
def record_payment(payment: schemas.PaymentCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission(["accounting", "payments"]))):
    """Enregistre un encaissement réel dans le tiroir-caisse."""
    assert_patient_access(payment.patient_id, current_user, db)
    
    new_payment = models.Payment(
        patient_id=payment.patient_id,
        amount=payment.amount,
        payment_method=getattr(models.PaymentMethod, payment.payment_method, models.PaymentMethod.ESPECES),
        payment_date=payment.payment_date or datetime.now(),
        acte_id=payment.acte_id,
        installment_id=payment.installment_id,
        notes=payment.notes,
        validated_by=f"{current_user.nom_complet or 'Utilisateur'} ({current_user.role})"
    )
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

@router.get("/payments/patient/{patient_id}", response_model=List[schemas.PaymentOut])
def get_patient_payments(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Récupère l'historique des encaissements d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.Payment).filter(models.Payment.patient_id == patient_id).order_by(models.Payment.payment_date.desc()).all()
@router.get("/accounting/honoraires", response_model=schemas.HonoraireListResponse)
def get_accounting_honoraires(patient_id: Optional[int] = None, assurance: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    user_employer_id = current_user.get_employer_id()
    
    # 1. Requête pour les documents (Notes d'honoraires)
    doc_query = db.query(models.DocumentArchive).join(models.Patient).filter(
        models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES, 
        or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
        or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None),
        or_(models.DocumentArchive.is_accounted == True, models.DocumentArchive.is_accounted == None),
        models.Patient.employer_id == user_employer_id
    )
    
    # 2. Requête pour les actes marqués pour la compta
    acte_query = db.query(models.Acte).join(models.Patient).filter(
        models.Acte.is_accounted == True,
        models.Patient.employer_id == user_employer_id
    )

    if patient_id: 
        doc_query = doc_query.filter(models.DocumentArchive.patient_id == patient_id)
        acte_query = acte_query.filter(models.Acte.patient_id == patient_id)
    if assurance: 
        doc_query = doc_query.filter(models.Patient.assurance == assurance)
        acte_query = acte_query.filter(models.Patient.assurance == assurance)
    if year: 
        doc_query = doc_query.filter(func.extract('year', models.DocumentArchive.created_at) == year)
        # Pour les actes on utilise date_debut
        acte_query = acte_query.filter(func.extract('year', models.Acte.date_debut) == year)
    if month: 
        doc_query = doc_query.filter(func.extract('month', models.DocumentArchive.created_at) == month)
        acte_query = acte_query.filter(func.extract('month', models.Acte.date_debut) == month)

    docs = doc_query.all()
    actes = acte_query.all()
    
    items = []
    total_amount = 0
    
    # Traitement des documents
    for doc in docs:
        amount = extract_amount_from_clinical_data(doc.clinical_data)
        items.append({
            "id": f"doc_{doc.id}", 
            "patient_id": doc.patient_id, 
            "patient_name": f"{doc.patient.nom} {doc.patient.prenom}", 
            "assurance": doc.patient.assurance or "AUCUNE", 
            "date": doc.created_at, 
            "title": doc.title or "Note d'honoraires", 
            "amount": amount, 
            "file_url": f"documents/{doc.id}/download",
            "payment_status": doc.payment_status or "EN_ATTENTE",
            "validated_by": doc.validated_by,
            "is_collected": doc.is_collected
        })
        total_amount += amount

    # Traitement des actes
    for acte in actes:
        items.append({
            "id": f"acte_{acte.id}",
            "patient_id": acte.patient_id,
            "patient_name": f"{acte.patient.nom} {acte.patient.prenom}",
            "assurance": acte.patient.assurance or "AUCUNE",
            "date": acte.date_debut,
            "title": f"Acte: {acte.libelle}",
            "amount": acte.montant,
            "file_url": "", # Pas de PDF pour un acte seul
            "payment_status": acte.statut_paiement or "EN_ATTENTE",
            "validated_by": acte.validated_by,
            "is_collected": acte.is_collected
        })
        total_amount += acte.montant

    # Tri par date décroissante
    items.sort(key=lambda x: x["date"], reverse=True)
    
    # 3. Calcul des encaissements réels (Recettes)
    payment_query = db.query(func.sum(models.Payment.amount)).join(models.Patient).filter(
        models.Patient.employer_id == user_employer_id
    )
    if patient_id: 
        payment_query = payment_query.filter(models.Payment.patient_id == patient_id)
    if assurance: 
        payment_query = payment_query.filter(models.Patient.assurance == assurance)
    if year: 
        payment_query = payment_query.filter(func.extract('year', models.Payment.payment_date) == year)
    if month: 
        payment_query = payment_query.filter(func.extract('month', models.Payment.payment_date) == month)
        
    total_collected = payment_query.scalar() or 0.0
    
    return {"total": len(items), "total_amount": total_amount, "total_collected": total_collected, "items": items}

@router.get("/accounting/treasury-hub")
async def get_treasury_hub(
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user)
):
    from backend.services.accounting_service import accounting_service
    return accounting_service.get_treasury_summary(db, user.get_employer_id())

@router.post("/accounting/encaisser/{item_id}")
async def mark_as_paid(
    item_id: str,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user)
):
    try:
        from backend.utils.access_control import assert_patient_access
        
        if item_id.startswith("doc_"):
            doc_id = int(item_id.split("_")[1])
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Document non trouvé")
            assert_patient_access(doc.patient_id, user, db)
            from backend.utils.accounting_utils import extract_amount_from_clinical_data

            doc.payment_status = models.PaiementStatut.PAYE
            doc.is_collected = True
            doc.validated_by = f"{user.nom_complet or 'Utilisateur'} ({user.role})"
            doc.updated_at = datetime.now()

            # Create corresponding Payment
            payment_obj = models.Payment(
                patient_id=doc.patient_id,
                amount=extract_amount_from_clinical_data(doc.clinical_data),
                payment_method="ESPECES",
                payment_date=doc.created_at,
                notes=f"Lien Doc ID: {doc.id}",
                validated_by=doc.validated_by
            )
            db.add(payment_obj)
            
        elif item_id.startswith("acte_"):
            acte_id = int(item_id.split("_")[1])
            acte = db.query(models.Acte).filter(models.Acte.id == acte_id).first()
            if not acte: raise HTTPException(status_code=404, detail="Acte non trouvé")
            assert_patient_access(acte.patient_id, user, db)
            acte.statut_paiement = models.PaiementStatut.PAYE
            acte.is_collected = True
            acte.validated_by = f"{user.nom_complet or 'Utilisateur'} ({user.role})"

            payment_obj = models.Payment(
                patient_id=acte.patient_id,
                amount=acte.montant,
                payment_method="ESPECES",
                payment_date=acte.date_debut,
                notes=f"Lien Acte ID: {acte.id}",
                validated_by=acte.validated_by
            )
            db.add(payment_obj)
            
        else:
            doc_id = int(item_id)
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Élément non trouvé")
            assert_patient_access(doc.patient_id, user, db)
            
            from backend.utils.accounting_utils import extract_amount_from_clinical_data
            doc.payment_status = models.PaiementStatut.PAYE
            doc.is_collected = True
            doc.validated_by = f"{user.nom_complet or 'Utilisateur'} ({user.role})"
            doc.updated_at = datetime.now()

            payment_obj = models.Payment(
                patient_id=doc.patient_id,
                amount=extract_amount_from_clinical_data(doc.clinical_data),
                payment_method="ESPECES",
                payment_date=doc.created_at,
                notes=f"Lien Doc ID: {doc.id}",
                validated_by=doc.validated_by
            )
            db.add(payment_obj)
            
        db.commit()
        return {"status": "success", "message": "Élément marqué comme encaissé"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/accounting/export-pdf")
def export_accounting_pdf(patient_id: Optional[int] = None, assurance: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    data = get_accounting_honoraires(patient_id, assurance, year, month, db, current_user)
    report_gen = ReportGenerator()
    filepath = report_gen.generate_accounting_report(items=data["items"], total_amount=data["total_amount"], filters={"assurance": assurance, "month": month, "year": year})
    return FileResponse(path=os.path.join(os.getcwd(), filepath), filename=f"Compta_{year or 'Global'}.pdf")

