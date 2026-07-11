from sqlalchemy import func, or_, and_
from typing import Optional, List, Dict
from fastapi.responses import FileResponse, StreamingResponse
import os, csv, io
from backend.services.generators.report_gen import ReportGenerator
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

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

    # Auto-sync statut de l'acte si le paiement est lié à un acte
    if payment.acte_id:
        acte = db.query(models.Acte).filter(models.Acte.id == payment.acte_id).first()
        if acte:
            total_paid = db.query(func.sum(models.Payment.amount)).filter(
                models.Payment.acte_id == payment.acte_id
            ).scalar() or 0.0
            if total_paid >= acte.montant:
                acte.statut_paiement = models.PaiementStatut.PAYE
                acte.is_collected = True
            elif total_paid > 0:
                acte.statut_paiement = models.PaiementStatut.PARTIEL
            db.commit()

    return new_payment

@router.get("/payments/patient/{patient_id}", response_model=List[schemas.PaymentOut])
def get_patient_payments(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    """Récupère l'historique des encaissements d'un patient."""
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.Payment).filter(models.Payment.patient_id == patient_id).order_by(models.Payment.payment_date.desc()).all()

@router.get("/actes-billing/patient/{patient_id}")
def get_patient_actes_billing(patient_id: int, db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))):
    """Retourne tous les actes du patient avec leur solde encaissé par acte (sans N+1)."""
    assert_patient_access(patient_id, current_user, db)
    actes = (db.query(models.Acte)
        .filter(models.Acte.patient_id == patient_id)
        .order_by(models.Acte.date_debut.desc())
        .all())
    paid_rows = (db.query(models.Payment.acte_id, func.sum(models.Payment.amount))
        .filter(models.Payment.patient_id == patient_id,
                models.Payment.acte_id != None)
        .group_by(models.Payment.acte_id)
        .all())
    paid_map = {aid: float(total) for aid, total in paid_rows}
    return [{
        "id":              a.id,
        "libelle":         a.libelle,
        "type_acte":       a.type_acte.value if a.type_acte else None,
        "montant":         a.montant,
        "total_paid":      paid_map.get(a.id, 0.0),
        "remaining_due":   max(round(a.montant - paid_map.get(a.id, 0.0), 2), 0.0),
        "statut_paiement": a.statut_paiement.value if a.statut_paiement else "EN_ATTENTE",
        "date_debut":      a.date_debut.isoformat() if a.date_debut else None,
        "is_accounted":    a.is_accounted,
    } for a in actes]

@router.get("/honoraires", response_model=schemas.HonoraireListResponse)
def get_accounting_honoraires(
    patient_id: Optional[int] = None, 
    assurance: Optional[str] = None, 
    year: Optional[int] = None, 
    month: Optional[int] = None, 
    filter_type: Optional[str] = "all",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    user_employer_id = current_user.get_employer_id()
    from backend.utils.accounting_utils import extract_amount_from_clinical_data
    
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

    if filter_type == "insured_notes_only":
        doc_query = doc_query.filter(models.Patient.assurance.isnot(None), models.Patient.assurance != "AUCUNE")
        acte_query = acte_query.filter(False) # On ignore les actes simples pour ce filtre
        
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
    summary_by_title = {}
    
    # Traitement des documents
    for doc in docs:
        amount = extract_amount_from_clinical_data(doc.clinical_data)
        
        # Extraction du vrai nom d'acte s'il existe dans payments ou items
        display_title = doc.title or "Note d'honoraires"
        if doc.clinical_data and isinstance(doc.clinical_data, dict):
            if 'items' in doc.clinical_data and isinstance(doc.clinical_data['items'], list) and len(doc.clinical_data['items']) > 0:
                display_title = doc.clinical_data['items'][0].get('titre', doc.clinical_data['items'][0].get('nom', display_title))
            elif 'payments' in doc.clinical_data and isinstance(doc.clinical_data['payments'], list) and len(doc.clinical_data['payments']) > 0:
                display_title = doc.clinical_data['payments'][0].get('motif', doc.clinical_data['payments'][0].get('description', display_title))

        items.append({
            "id": f"doc_{doc.id}", 
            "patient_id": doc.patient_id, 
            "patient_name": f"{doc.patient.nom} {doc.patient.prenom}", 
            "assurance": doc.patient.assurance or "AUCUNE", 
            "date": doc.created_at, 
            "title": display_title, 
            "amount": amount, 
            "file_url": f"documents/{doc.id}/download",
            "payment_status": doc.payment_status or "EN_ATTENTE",
            "validated_by": doc.validated_by,
            "is_collected": doc.is_collected
        })
        total_amount += amount
        summary_by_title[display_title] = summary_by_title.get(display_title, 0) + amount

    # Traitement des actes
    for acte in actes:
        display_title = f"{acte.libelle}"
        items.append({
            "id": f"acte_{acte.id}",
            "patient_id": acte.patient_id,
            "patient_name": f"{acte.patient.nom} {acte.patient.prenom}",
            "assurance": acte.patient.assurance or "AUCUNE",
            "date": acte.date_debut,
            "title": display_title,
            "amount": acte.montant,
            "file_url": "", # Pas de PDF pour un acte seul
            "payment_status": acte.statut_paiement or "EN_ATTENTE",
            "validated_by": acte.validated_by,
            "is_collected": acte.is_collected
        })
        total_amount += acte.montant
        summary_by_title[display_title] = summary_by_title.get(display_title, 0) + acte.montant

    # Tri par date décroissante
    items.sort(key=lambda x: x["date"], reverse=True)
    
    # 3. Calcul des encaissements réels (Recettes)
    payment_query = db.query(func.sum(models.Payment.amount)).join(models.Patient).filter(
        models.Patient.employer_id == user_employer_id
    )
    if filter_type == "insured_notes_only":
        payment_query = payment_query.filter(models.Patient.assurance.isnot(None), models.Patient.assurance != "AUCUNE")
    
    if patient_id: 
        payment_query = payment_query.filter(models.Payment.patient_id == patient_id)
    if assurance: 
        payment_query = payment_query.filter(models.Patient.assurance == assurance)
    if year: 
        payment_query = payment_query.filter(func.extract('year', models.Payment.payment_date) == year)
    if month: 
        payment_query = payment_query.filter(func.extract('month', models.Payment.payment_date) == month)
        
    total_collected = payment_query.scalar() or 0.0
    
    return {
        "total": len(items), 
        "total_amount": total_amount, 
        "total_collected": total_collected, 
        "items": items,
        "summary_by_title": summary_by_title
    }

@router.get("/treasury-hub")
async def get_treasury_hub(
    db: Session = Depends(database.get_db),
    user: models.User = Depends(require_permission("accounting"))
):
    from backend.services.accounting_service import accounting_service
    return accounting_service.get_treasury_summary(db, user.get_employer_id())

@router.post("/encaisser/{item_id}")
async def mark_as_paid(
    item_id: str,
    payment_method: str = Body(default="ESPECES", embed=True),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(require_permission(["accounting", "payments"]))
):
    try:
        from backend.utils.access_control import assert_patient_access
        
        now = datetime.now()
        
        if item_id.startswith("doc_"):
            doc_id = int(item_id.split("_")[1])
            doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
            if not doc: raise HTTPException(status_code=404, detail="Document non trouvé")
            assert_patient_access(doc.patient_id, user, db)
            from backend.utils.accounting_utils import extract_amount_from_clinical_data

            doc.payment_status = models.PaiementStatut.PAYE
            doc.is_collected = True
            doc.validated_by = f"{user.nom_complet or 'Utilisateur'} ({user.role})"
            doc.updated_at = now

            # Create corresponding Payment
            payment_obj = models.Payment(
                patient_id=doc.patient_id,
                amount=extract_amount_from_clinical_data(doc.clinical_data),
                payment_method=payment_method,
                payment_date=now,
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
                payment_method=payment_method,
                payment_date=now,
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
            doc.updated_at = now

            payment_obj = models.Payment(
                patient_id=doc.patient_id,
                amount=extract_amount_from_clinical_data(doc.clinical_data),
                payment_method=payment_method,
                payment_date=now,
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

@router.get("/export-pdf")
def export_accounting_pdf(patient_id: Optional[int] = None, assurance: Optional[str] = None, year: Optional[int] = None, month: Optional[int] = None, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("accounting"))):
    data = get_accounting_honoraires(patient_id, assurance, year, month, db=db, current_user=current_user)
    report_gen = ReportGenerator()
    filepath = report_gen.generate_accounting_report(items=data["items"], total_amount=data["total_amount"], filters={"assurance": assurance, "month": month, "year": year})
    return FileResponse(path=os.path.join(os.getcwd(), filepath), filename=f"Compta_{year or 'Global'}.pdf")


@router.patch("/item/{item_id}")
def update_honoraire_item(
    item_id: str,
    updates: dict = Body(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    """Met à jour le titre et/ou le montant d'une note d'honoraires ou d'un acte."""
    new_title: str | None = updates.get("title")
    new_amount: float | None = updates.get("amount")

    if new_title is not None and len(new_title.strip()) == 0:
        raise HTTPException(status_code=422, detail="Le titre ne peut pas être vide")
    if new_amount is not None and new_amount < 0:
        raise HTTPException(status_code=422, detail="Le montant ne peut pas être négatif")

    if item_id.startswith("doc_"):
        doc_id = int(item_id.split("_")[1])
        doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document introuvable")
        assert_patient_access(doc.patient_id, current_user, db)
        if new_title is not None:
            doc.title = new_title.strip()
            if isinstance(doc.clinical_data, dict):
                if "items" in doc.clinical_data and isinstance(doc.clinical_data["items"], list) and doc.clinical_data["items"]:
                    doc.clinical_data["items"][0]["titre"] = new_title.strip()
        if new_amount is not None:
            if isinstance(doc.clinical_data, dict):
                if "items" in doc.clinical_data and isinstance(doc.clinical_data["items"], list) and doc.clinical_data["items"]:
                    doc.clinical_data["items"][0]["montant"] = new_amount
                elif "payments" in doc.clinical_data and isinstance(doc.clinical_data["payments"], list) and doc.clinical_data["payments"]:
                    doc.clinical_data["payments"][0]["montant"] = new_amount
                else:
                    doc.clinical_data["montant"] = new_amount
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(doc, "clinical_data")
        doc.updated_at = datetime.now()

    elif item_id.startswith("acte_"):
        acte_id = int(item_id.split("_")[1])
        acte = db.query(models.Acte).filter(models.Acte.id == acte_id).first()
        if not acte:
            raise HTTPException(status_code=404, detail="Acte introuvable")
        assert_patient_access(acte.patient_id, current_user, db)
        if new_title is not None:
            acte.libelle = new_title.strip()
        if new_amount is not None:
            acte.montant = new_amount
    else:
        raise HTTPException(status_code=400, detail="Identifiant invalide")

    db.commit()
    return {"status": "success", "id": item_id, "title": new_title, "amount": new_amount}


@router.get("/export-csv")
def export_accounting_csv(
    patient_id: Optional[int] = None,
    assurance: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    filter_type: Optional[str] = "all",
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    data = get_accounting_honoraires(patient_id, assurance, year, month, filter_type, db=db, current_user=current_user)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Date", "Patient", "Assurance", "Acte / Note", "Montant (MAD)", "Statut", "Encaissé", "Validé par"])
    for item in data["items"]:
        date_str = item["date"].strftime("%d/%m/%Y") if hasattr(item["date"], "strftime") else str(item["date"])[:10]
        writer.writerow([
            date_str,
            item["patient_name"],
            item["assurance"],
            item["title"],
            str(item["amount"]).replace(".", ","),
            item["payment_status"],
            "Oui" if item.get("is_collected") else "Non",
            item.get("validated_by") or "",
        ])
    writer.writerow([])
    writer.writerow(["", "", "", "TOTAL FACTURÉ", str(data["total_amount"]).replace(".", ",")])
    writer.writerow(["", "", "", "TOTAL ENCAISSÉ", str(data["total_collected"]).replace(".", ",")])

    filename = f"Compta_{year or 'Global'}_{month or 'Annuel'}.csv"
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/send-email/{item_id}")
def send_honoraire_by_email(
    item_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    """Envoie la note d'honoraires par email au patient."""
    from backend.services.email_service import email_service

    patient = None
    doc_id = None

    if item_id.startswith("doc_"):
        doc_id = int(item_id.split("_")[1])
        doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document introuvable")
        assert_patient_access(doc.patient_id, current_user, db)
        patient = doc.patient
    elif item_id.startswith("acte_"):
        acte_id = int(item_id.split("_")[1])
        acte = db.query(models.Acte).filter(models.Acte.id == acte_id).first()
        if not acte:
            raise HTTPException(status_code=404, detail="Acte introuvable")
        assert_patient_access(acte.patient_id, current_user, db)
        patient = acte.patient
    else:
        raise HTTPException(status_code=400, detail="Identifiant invalide")

    if not patient or not patient.email:
        raise HTTPException(status_code=422, detail="Ce patient n'a pas d'adresse email renseignée")

    cabinet_name = getattr(current_user, "nom_complet", None) or "votre cabinet dentaire"
    subject = f"Note d'honoraires — {cabinet_name}"
    text = (
        f"Bonjour {patient.prenom} {patient.nom},\n\n"
        f"Veuillez trouver ci-joint votre note d'honoraires émise par {cabinet_name}.\n\n"
        "Pour toute question, n'hésitez pas à nous contacter.\n\nCordialement."
    )
    html = (
        f"<p>Bonjour <strong>{patient.prenom} {patient.nom}</strong>,</p>"
        f"<p>Veuillez trouver ci-joint votre note d'honoraires émise par <strong>{cabinet_name}</strong>.</p>"
        "<p>Pour toute question, n'hésitez pas à nous contacter.</p>"
        "<p>Cordialement.</p>"
    )

    sent = email_service.send_email(patient.email, subject, text, html)
    if not sent:
        raise HTTPException(status_code=500, detail="Échec de l'envoi de l'email")
    return {"status": "success", "message": f"Email envoyé à {patient.email}"}


@router.get("/overdue")
def get_overdue_items(
    days: int = 30,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    """Retourne les notes d'honoraires non réglées depuis plus de `days` jours."""
    emp_id = current_user.get_employer_id()
    cutoff = datetime.now() - timedelta(days=days)

    overdue_docs = (
        db.query(models.DocumentArchive)
        .join(models.Patient)
        .filter(
            models.Patient.employer_id == emp_id,
            models.DocumentArchive.document_type == models.DocumentType.NOTE_HONORAIRES,
            models.DocumentArchive.payment_status == models.PaiementStatut.EN_ATTENTE,
            models.DocumentArchive.created_at <= cutoff,
        )
        .order_by(models.DocumentArchive.created_at.asc())
        .all()
    )

    from backend.utils.accounting_utils import extract_amount_from_clinical_data
    items = []
    for doc in overdue_docs:
        days_overdue = (datetime.now() - doc.created_at).days
        items.append({
            "id": f"doc_{doc.id}",
            "patient_id": doc.patient_id,
            "patient_name": f"{doc.patient.nom} {doc.patient.prenom}",
            "patient_email": doc.patient.email or None,
            "date": doc.created_at,
            "amount": extract_amount_from_clinical_data(doc.clinical_data),
            "days_overdue": days_overdue,
        })

    return {"total": len(items), "total_amount": sum(i["amount"] for i in items), "items": items}


@router.post("/relance/{item_id}")
def send_relance(
    item_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    """Envoie une relance de paiement par email au patient."""
    from backend.services.email_service import email_service

    if not item_id.startswith("doc_"):
        raise HTTPException(status_code=400, detail="Relances disponibles uniquement pour les notes d'honoraires")

    doc_id = int(item_id.split("_")[1])
    doc = db.query(models.DocumentArchive).filter(models.DocumentArchive.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    assert_patient_access(doc.patient_id, current_user, db)

    patient = doc.patient
    if not patient or not patient.email:
        raise HTTPException(status_code=422, detail="Ce patient n'a pas d'adresse email renseignée")

    from backend.utils.accounting_utils import extract_amount_from_clinical_data
    amount = extract_amount_from_clinical_data(doc.clinical_data)
    date_str = doc.created_at.strftime("%d/%m/%Y")
    cabinet_name = getattr(current_user, "nom_complet", None) or "votre cabinet dentaire"

    subject = f"Rappel de paiement — {cabinet_name}"
    text = (
        f"Bonjour {patient.prenom} {patient.nom},\n\n"
        f"Nous vous rappelons qu'une note d'honoraires du {date_str} d'un montant de {amount:,.2f} MAD "
        f"reste en attente de règlement auprès de {cabinet_name}.\n\n"
        "Merci de régulariser votre situation dans les meilleurs délais.\n\nCordialement."
    )
    html = (
        f"<p>Bonjour <strong>{patient.prenom} {patient.nom}</strong>,</p>"
        f"<p>Nous vous rappelons qu'une note d'honoraires du <strong>{date_str}</strong> "
        f"d'un montant de <strong>{amount:,.2f} MAD</strong> reste en attente de règlement "
        f"auprès de <strong>{cabinet_name}</strong>.</p>"
        "<p>Merci de régulariser votre situation dans les meilleurs délais.</p>"
        "<p>Cordialement.</p>"
    )

    sent = email_service.send_email(patient.email, subject, text, html)
    if not sent:
        raise HTTPException(status_code=500, detail="Échec de l'envoi de la relance")
    return {"status": "success", "message": f"Relance envoyée à {patient.email}"}


@router.get("/patient-debts")
def get_patient_debts(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("accounting"))
):
    """Liste les patients avec solde impayé (total actes − total paiements), triés par montant décroissant."""
    employer_id = current_user.get_employer_id()

    billed_rows = (
        db.query(models.Acte.patient_id, func.sum(models.Acte.montant).label("total"))
        .join(models.Patient, models.Acte.patient_id == models.Patient.id)
        .filter(models.Patient.employer_id == employer_id)
        .group_by(models.Acte.patient_id)
        .all()
    )
    paid_rows = (
        db.query(models.Payment.patient_id, func.sum(models.Payment.amount).label("total"))
        .join(models.Patient, models.Payment.patient_id == models.Patient.id)
        .filter(models.Patient.employer_id == employer_id)
        .group_by(models.Payment.patient_id)
        .all()
    )

    billed_map = {pid: float(total) for pid, total in billed_rows}
    paid_map   = {pid: float(total) for pid, total in paid_rows}

    debtor_ids = [
        pid for pid in billed_map
        if billed_map[pid] - paid_map.get(pid, 0.0) > 0.01
    ]

    if not debtor_ids:
        return {"total_patients": 0, "total_amount": 0.0, "items": []}

    patients = (
        db.query(models.Patient)
        .filter(models.Patient.id.in_(debtor_ids), models.Patient.employer_id == employer_id)
        .all()
    )

    items = [
        {
            "patient_id": p.id,
            "nom": p.nom,
            "prenom": p.prenom,
            "telephone": p.telephone,
            "assurance": getattr(p, 'assurance', None),
            "total_billed": round(billed_map[p.id], 2),
            "total_paid": round(paid_map.get(p.id, 0.0), 2),
            "remaining_due": round(billed_map[p.id] - paid_map.get(p.id, 0.0), 2),
        }
        for p in patients
    ]
    items.sort(key=lambda x: x["remaining_due"], reverse=True)

    return {
        "total_patients": len(items),
        "total_amount": round(sum(i["remaining_due"] for i in items), 2),
        "items": items,
    }

