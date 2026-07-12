import logging
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, Response, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

from backend import models, schemas, database
from backend.routers.auth import get_current_user, require_permission, is_superadmin_user
from backend.utils.access_control import assert_patient_access

router = APIRouter(tags=["Patients"])

# --- HELPERS ---

def check_duplicate_patient(db: Session, nom: str, prenom: str, date_naissance: datetime, exclude_id: int = None) -> models.Patient:
    query = db.query(models.Patient).filter(
        func.lower(models.Patient.nom) == nom.lower().strip(),
        func.lower(models.Patient.prenom) == prenom.lower().strip(),
        models.Patient.date_naissance == date_naissance,
        models.Patient.deleted_at.is_(None),
    )
    if exclude_id:
        query = query.filter(models.Patient.id != exclude_id)
    return query.first()

import re

def generate_next_dossier_number(db: Session, employer_id: int) -> str:
    dossiers = db.query(models.Patient.numero_dossier).filter(
        models.Patient.employer_id == employer_id,
        models.Patient.numero_dossier.isnot(None)
    ).all()
    
    max_num = 0
    for (dossier,) in dossiers:
        if not dossier: continue
        numbers = re.findall(r'\d+', str(dossier))
        if numbers:
            try:
                # Extraire le dernier nombre trouvé dans la chaîne
                num = int(numbers[-1])
                if num > max_num:
                    max_num = num
            except ValueError:
                logger.debug("Impossible d'extraire un numéro de dossier depuis : %s", dossier)

    next_num = max_num + 1
    return str(next_num)


# --- ROUTES CRUD ---

@router.get("/next-dossier-number")
def get_next_dossier_number(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    return {"next_number": generate_next_dossier_number(db, current_user.get_employer_id())}

@router.get("/check-dossier/{numero}")
def check_dossier_availability(numero: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    exists = db.query(models.Patient).filter(
        models.Patient.numero_dossier == numero,
        models.Patient.employer_id == current_user.get_employer_id()
    ).first()
    return {
        "exists": bool(exists),
        "patient_id": exists.id if exists else None,
        "patient_name": f"{exists.nom.upper()} {exists.prenom.capitalize()}" if exists else None
    }

from pydantic import BaseModel
class DuplicateCheckRequest(BaseModel):
    nom: str
    prenom: str
    date_naissance: datetime
    exclude_id: Optional[int] = None

@router.post("/check-duplicate")
def check_duplicate_api(payload: DuplicateCheckRequest, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    existing = check_duplicate_patient(db, payload.nom, payload.prenom, payload.date_naissance, payload.exclude_id)
    return {
        "has_duplicate": bool(existing),
        "existing_patient": {
            "id": existing.id,
            "nom": existing.nom,
            "prenom": existing.prenom,
            "date_naissance": existing.date_naissance.strftime("%Y-%m-%d"),
            "created_at": existing.created_at.isoformat() if hasattr(existing, "created_at") and existing.created_at else None,
        } if existing else None,
    }

@router.get("/", response_model=List[schemas.PatientOut],
    summary="Lister les patients",
    description="Retourne tous les patients du cabinet (multi-tenant isolé). Supporte la recherche par nom/prénom/dossier. Header X-Total-Count disponible pour la pagination future.")
def read_patients(
    response: Response,
    skip: int = 0,
    limit: int = 1000,
    search: Optional[str] = None,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    user_employer_id = current_user.get_employer_id()
    base_query = db.query(models.Patient).filter(
        models.Patient.employer_id == user_employer_id,
        models.Patient.deleted_at.is_(None),
    )
    if search:
        search_term = f"%{search.strip()}%"
        base_query = base_query.filter(
            or_(
                models.Patient.nom.ilike(search_term),
                models.Patient.prenom.ilike(search_term),
                models.Patient.numero_dossier.ilike(search_term)
            )
        )
    total = base_query.count()
    response.headers["X-Total-Count"] = str(total)
    patients = base_query.options(joinedload(models.Patient.dossier)).offset(skip).limit(limit).all()
    return patients

from backend.services.audit_service import audit_service

@router.post("/", response_model=schemas.PatientOut,
    summary="Créer un patient",
    description="Crée un nouveau dossier patient avec détection de doublons (nom + prénom + date naissance). Passer `force_create=true` pour ignorer l'alerte doublon.")
def create_patient(patient: schemas.PatientCreate, force_create: bool = False, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    existing = check_duplicate_patient(db, patient.nom, patient.prenom, patient.date_naissance)
    if existing and not force_create:
        raise HTTPException(status_code=409, detail={"message": "Doublon détecté", "existing_patient": {"id": existing.id}})
    
    patient_data = patient.model_dump() if hasattr(patient, 'model_dump') else patient.dict()
    is_ortho_active = patient_data.pop('is_ortho_active', False)
    
    patient_data['nom'] = patient_data['nom'].upper().strip()
    patient_data['prenom'] = patient_data['prenom'].capitalize().strip()
    
    employer_id = current_user.get_employer_id()
    patient_data['employer_id'] = employer_id
    
    if not patient_data.get('numero_dossier'):
        patient_data['numero_dossier'] = generate_next_dossier_number(db, employer_id)
    
    db_patient = models.Patient(**patient_data)
    db.add(db_patient); db.flush()
    db.add(models.DossierClinique(patient_id=db_patient.id, is_ortho_active=is_ortho_active))
    
    # Audit log
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="CREATE",
        resource_type="Patient",
        resource_id=str(db_patient.id),
        details=f"Creation du patient {db_patient.nom} {db_patient.prenom} (Dossier: {db_patient.numero_dossier})"
    )
    
    db.commit(); db.refresh(db_patient)
    return db_patient

@router.get("/fantomes")
def get_fantome_patients(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """A1 — Patients fantômes : traitement actif + aucun RDV futur."""
    from sqlalchemy import exists, and_, desc as _desc
    employer_id = current_user.get_employer_id()
    now = datetime.now()
    cutoff_90d = now - timedelta(days=90)

    # IDs ortho actifs
    ortho_ids = {
        row[0] for row in db.query(models.DossierClinique.patient_id).join(
            models.Patient, models.Patient.id == models.DossierClinique.patient_id
        ).filter(
            models.Patient.employer_id == employer_id,
            models.DossierClinique.is_ortho_active == True
        ).all()
    }

    # IDs avec acte récent
    recent_ids = {
        row[0] for row in db.query(models.Acte.patient_id).join(
            models.Patient, models.Patient.id == models.Acte.patient_id
        ).filter(
            models.Patient.employer_id == employer_id,
            models.Acte.date_debut >= cutoff_90d
        ).distinct().all()
    }

    active_ids = ortho_ids | recent_ids
    if not active_ids:
        return []

    # Ceux qui ont un RDV futur non-annulé
    has_future_rdv = {
        row[0] for row in db.query(models.Appointment.patient_id).filter(
            models.Appointment.patient_id.in_(active_ids),
            models.Appointment.datetime_start > now,
            models.Appointment.status != "ANNULÉ"
        ).distinct().all()
    }

    fantome_ids = active_ids - has_future_rdv
    if not fantome_ids:
        return []

    fantomes = []
    for pid in fantome_ids:
        last_appt = db.query(models.Appointment).filter(
            models.Appointment.patient_id == pid,
            models.Appointment.datetime_start <= now,
            models.Appointment.status != "ANNULÉ"
        ).order_by(_desc(models.Appointment.datetime_start)).first()
        days_since = (now - last_appt.datetime_start).days if last_appt else None
        fantomes.append({
            "patient_id": pid,
            "days_since_last_appt": days_since,
            "is_ortho_active": pid in ortho_ids,
        })
    return fantomes


from backend.services.patient_scoring_service import patient_scoring_service


@router.get("/scores")
def get_patients_scores(db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    """Scores de TOUS les patients du cabinet en UN appel (batch agrégé) — évite N appels /score."""
    employer_id = current_user.get_employer_id()
    scores = patient_scoring_service.calculate_scores_bulk(db, employer_id)

    patients = db.query(
        models.Patient.id, models.Patient.manual_grade, models.Patient.grade_comment
    ).filter(models.Patient.employer_id == employer_id).all()

    result = {}
    for pid, manual_grade, comment in patients:
        s = scores.get(pid)
        if not s:
            continue
        result[pid] = {
            "score": s["score"],
            "grade": manual_grade or s["grade"],
            "is_manual": bool(manual_grade),
            "comment": comment,
            "details": s["details"],
        }
    return result


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def read_patient(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient or patient.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    return patient

@router.get("/{patient_id}/score")
def get_patient_score(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    
    # 1. Obtenir le score via le Service Métier dédié
    score_data = patient_scoring_service.calculate_score(db, patient_id)
    
    # 2. Détermination du Grade (Priorité au Manuel)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    is_manual = False
    grade = score_data["grade"]
    
    if patient and patient.manual_grade:
        grade = patient.manual_grade
        is_manual = True
        
    return {
        "score": score_data["score"],
        "grade": grade,
        "is_manual": is_manual,
        "comment": patient.grade_comment if patient else None,
        "details": score_data["details"]
    }

@router.patch("/{patient_id}/grade")
def update_patient_grade(patient_id: int, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient non trouvé")
        
    if "grade" in data:
        # None signifie retour au mode automatique
        patient.manual_grade = data["grade"]
    if "comment" in data:
        patient.grade_comment = data["comment"]
        
    db.commit()
    return {"status": "success"}

@router.patch("/{patient_id}/ortho")
def update_patient_ortho(patient_id: int, data: dict, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    dossier = db.query(models.DossierClinique).filter(models.DossierClinique.patient_id == patient_id).first()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier non trouvé")
        
    if "is_ortho_active" in data:
        dossier.is_ortho_active = data["is_ortho_active"]
        
    db.commit()
    return {"status": "success", "is_ortho_active": dossier.is_ortho_active}

# --- CLINICAL INTELLIGENCE ---

@router.get("/{patient_id}/documents")
def get_patient_documents(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()

    # 1. BDD
    docs = db.query(models.DocumentArchive).filter(
        models.DocumentArchive.patient_id == patient_id,
        or_(models.DocumentArchive.status == models.DocumentStatus.ACTIF, models.DocumentArchive.status == None),
        or_(models.DocumentArchive.is_latest_version == True, models.DocumentArchive.is_latest_version == None)
    ).order_by(models.DocumentArchive.created_at.desc()).all()
    
    from backend.core.media_paths import get_media_root
    MEDIA_DIR = get_media_root()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    results = []
    for doc in docs:
        rel_path = doc.file_path.split('static/')[-1]
        
        if doc.file_path.startswith("static/archives/") or doc.file_path.startswith("static/documents/"):
            abs_path = str(MEDIA_DIR / doc.file_path.replace("static/", "", 1))
        else:
            abs_path = os.path.join(BASE_DIR, doc.file_path)
            
        results.append({
            "id": str(doc.id), "name": doc.original_filename, "type": doc.document_type.value,
            "date": doc.created_at.strftime("%d/%m/%Y"), "url": f"static/{rel_path}",
            "clinical_data": doc.clinical_data, "timestamp": doc.created_at.timestamp(),
            "file_exists": os.path.isfile(abs_path),
        })
        
    # 2. Legacy
    static_dir = os.path.join(BASE_DIR, "static")
    p_folder = f"{patient.id}_{patient.nom.upper()}_{patient.prenom.capitalize()}"
    legacy_dir = os.path.join(static_dir, "patients", p_folder, "Documents")
    
    if os.path.exists(legacy_dir):
        for f in os.listdir(legacy_dir):
            if f.endswith(".pdf"):
                results.append({
                    "id": f"legacy:{patient_id}:{f}", "name": f, "type": "LEGACY",
                    "date": "Ancien", "url": f"static/patients/{p_folder}/Documents/{f}",
                    "timestamp": os.path.getmtime(os.path.join(legacy_dir, f)),
                    "file_exists": True,
                })
    results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return results

@router.get("/{patient_id}/appointment-intel")
def get_patient_intel(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    devis = db.query(models.DocumentArchive).filter(models.DocumentArchive.patient_id == patient_id, models.DocumentArchive.document_type == models.DocumentType.DEVIS).all()
    p_acts = db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == patient_id).scalar() or 0.0
    p_pays = db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == patient_id).scalar() or 0.0
    solde_attente = max(float(p_acts) - float(p_pays), 0.0)
    return {
        "suggestion": "Suite de traitement" if devis else "Consultation",
        "duration": 45 if devis else 30,
        "has_active_plan": bool(devis),
        "solde_attente": round(float(solde_attente), 2),
    }

@router.get("/{patient_id}/analyses", response_model=List[schemas.CephaloAnalysisOut])
def get_patient_analyses(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    return db.query(models.CephaloAnalysis).filter(models.CephaloAnalysis.patient_id == patient_id).all()

# --- CLINICAL INTELLIGENCE V2.0 ---

@router.get("/{patient_id}/ai-summary")
def get_patient_ai_summary(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("clinical"))):
    """Module 2 — Résumé Flash Patient (P0)."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services.clinical_intelligence import clinical_intel
    return clinical_intel.get_patient_summary(db, patient_id)

@router.get("/{patient_id}/ai-diagnostic")
def get_patient_ai_diagnostic(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("clinical"))):
    """Module 3 — Panneau Conseil Clinique (P2)."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services.clinical_intelligence import clinical_intel
    return clinical_intel.get_full_diagnostic(db, patient_id)

@router.get("/{patient_id}/cmo-synthesis")
def get_patient_cmo_synthesis(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("clinical"))):
    """Agent Multimodal — Chief Medical Officer (Synthèse Pano + Cephalo)."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services.cmo_agent_service import cmo_agent
    return cmo_agent.generate_global_synthesis(db, patient_id, current_user.id)

@router.get("/{patient_id}/financial-snapshot")
def get_patient_financial_snapshot(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    """Snapshot financier complet d'un patient : facturé, encaissé, reste dû, impayés, échéances."""
    assert_patient_access(patient_id, current_user, db)

    from datetime import date as date_type
    today = date_type.today()

    total_billed = float(
        db.query(func.sum(models.Acte.montant)).filter(models.Acte.patient_id == patient_id).scalar() or 0.0
    )
    total_collected = float(
        db.query(func.sum(models.Payment.amount)).filter(models.Payment.patient_id == patient_id).scalar() or 0.0
    )
    remaining_due = max(total_billed - total_collected, 0.0)

    overdue_actes = (
        db.query(models.Acte)
        .filter(
            models.Acte.patient_id == patient_id,
            models.Acte.statut_paiement.in_(["EN_ATTENTE", "A_ENCAISSER", "PARTIEL"]),
        )
        .order_by(models.Acte.date_debut.desc())
        .limit(10)
        .all()
    )
    overdue_total = sum(float(a.montant) for a in overdue_actes)
    overdue_items = [
        {
            "id": a.id,
            "libelle": a.libelle,
            "montant": float(a.montant),
            "statut_paiement": a.statut_paiement,
            "date_debut": a.date_debut.isoformat() if a.date_debut else None,
            "type_acte": a.type_acte,
        }
        for a in overdue_actes
    ]

    upcoming_installments = (
        db.query(models.Installment)
        .join(models.InstallmentPlan, models.Installment.plan_id == models.InstallmentPlan.id)
        .filter(
            models.InstallmentPlan.patient_id == patient_id,
            models.Installment.status == "EN_ATTENTE",
            models.Installment.due_date >= today,
        )
        .order_by(models.Installment.due_date)
        .limit(5)
        .all()
    )
    upcoming_total = sum(float(i.amount) for i in upcoming_installments)
    upcoming_list = [
        {
            "id": i.id,
            "label": i.label,
            "amount": float(i.amount),
            "due_date": i.due_date.isoformat() if i.due_date else None,
        }
        for i in upcoming_installments
    ]

    recent_payments = (
        db.query(models.Payment)
        .filter(models.Payment.patient_id == patient_id)
        .order_by(models.Payment.payment_date.desc())
        .limit(5)
        .all()
    )
    recent_list = [
        {
            "id": p.id,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "payment_date": p.payment_date.isoformat() if p.payment_date else None,
            "notes": p.notes,
        }
        for p in recent_payments
    ]

    methods_rows = (
        db.query(
            models.Payment.payment_method,
            func.sum(models.Payment.amount).label("total"),
            func.count(models.Payment.id).label("count"),
        )
        .filter(models.Payment.patient_id == patient_id)
        .group_by(models.Payment.payment_method)
        .all()
    )
    payment_methods = {
        str(m.payment_method): {"total": float(m.total), "count": int(m.count)}
        for m in methods_rows
    }

    return {
        "total_billed": round(total_billed, 2),
        "total_collected": round(total_collected, 2),
        "remaining_due": round(remaining_due, 2),
        "overdue_count": len(overdue_items),
        "overdue_total": round(overdue_total, 2),
        "upcoming_installments_count": len(upcoming_list),
        "upcoming_installments_total": round(upcoming_total, 2),
        "upcoming_installments": upcoming_list,
        "recent_payments": recent_list,
        "overdue_items": overdue_items,
        "payment_methods": payment_methods,
    }


# --- TREATMENT JOURNEY ---

_MILESTONE_PHYSICIAN_ONLY = {
    schemas.MilestoneType.DIAGNOSTIC,
    schemas.MilestoneType.CONTROLE,
    schemas.MilestoneType.CLOTURE,
}


def _assert_milestone_authorized(milestone_type: schemas.MilestoneType, current_user: models.User):
    """Matrice de permissions par type de jalon — DIAGNOSTIC/CONTROLE/CLOTURE réservés au
    dentiste/admin ; DEVIS_VALIDE autorisé aussi aux sous-comptes avec la permission accounting.
    Reprend l'idiome déjà utilisé en ligne 709 (suppression de patient)."""
    if is_superadmin_user(current_user):
        return
    role_value = current_user.role.value if hasattr(current_user.role, "value") else current_user.role
    is_owner_role = bool(current_user.role) and role_value in ("DENTISTE", "ADMIN")

    if milestone_type in _MILESTONE_PHYSICIAN_ONLY:
        if not is_owner_role:
            raise HTTPException(status_code=403, detail="Seul un dentiste/admin peut créer ou supprimer ce type de jalon.")
        return

    # DEVIS_VALIDE : dentiste/admin OU permission accounting explicite
    if is_owner_role:
        return
    perms = current_user.permissions or {}
    if not perms.get("accounting", False):
        raise HTTPException(status_code=403, detail="Vous n'avez pas l'autorisation de valider un devis.")


@router.get("/{patient_id}/journey", response_model=schemas.PatientJourneyResponse)
def get_patient_journey(
    patient_id: int,
    full_history: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """Fil chronologique du parcours patient — agrège 9 sources en lecture seule."""
    assert_patient_access(patient_id, current_user, db)
    from backend.services import patient_journey_service
    return patient_journey_service.build_journey(db, patient_id, current_user.get_employer_id(), full_history)


@router.post("/{patient_id}/journey/milestones", response_model=schemas.JourneyMilestoneCreateResponse, status_code=status.HTTP_201_CREATED)
def create_patient_journey_milestone(
    patient_id: int,
    payload: schemas.JourneyMilestoneCreate,
    response: Response,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    assert_patient_access(patient_id, current_user, db)
    _assert_milestone_authorized(payload.milestone_type, current_user)

    from backend.services import patient_journey_service
    from backend.services.audit_service import audit_service

    result = patient_journey_service.check_and_create_milestone(
        db, patient_id, current_user.get_employer_id(),
        models.MilestoneType(payload.milestone_type.value), payload.milestone_date,
        payload.note, payload.confirm_duplicate, current_user.id,
    )

    if result.milestone is None:
        response.status_code = status.HTTP_200_OK
        return result

    audit_service.log(
        db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(),
        action="CREATE", resource_type="JourneyMilestone", resource_id=str(result.milestone.id),
        details=(
            f"type={payload.milestone_type.value} date={payload.milestone_date} patient={patient_id} "
            f"note_present={bool(payload.note)} note_length={len(payload.note) if payload.note else 0}"
        ),
    )
    return result


@router.delete("/{patient_id}/journey/milestones/{milestone_id}")
def delete_patient_journey_milestone(
    patient_id: int,
    milestone_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    assert_patient_access(patient_id, current_user, db)

    milestone = (
        db.query(models.JourneyMilestone)
        .filter(
            models.JourneyMilestone.id == milestone_id,
            models.JourneyMilestone.patient_id == patient_id,
            models.JourneyMilestone.deleted_at.is_(None),
        )
        .first()
    )
    if milestone is None:
        raise HTTPException(status_code=404, detail="Jalon introuvable.")

    _assert_milestone_authorized(schemas.MilestoneType(milestone.milestone_type.value), current_user)

    snapshot_note = milestone.note
    from backend.services import patient_journey_service
    from backend.services.audit_service import audit_service

    patient_journey_service.soft_delete_milestone(db, patient_id, milestone_id, current_user.id)

    audit_service.log(
        db=db, user_id=current_user.id, employer_id=current_user.get_employer_id(),
        action="DELETE", resource_type="JourneyMilestone", resource_id=str(milestone_id),
        details=(
            f"milestone_id={milestone_id} patient_id={patient_id} type={milestone.milestone_type.value} "
            f"date={milestone.milestone_date} created_by={milestone.created_by} created_at={milestone.created_at} "
            f"note_present={bool(snapshot_note)} note_length={len(snapshot_note) if snapshot_note else 0}"
        ),
    )
    return {"status": "deleted", "id": milestone_id}


@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(patient_id: int, patient_update: schemas.PatientUpdate, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("patients"))):
    assert_patient_access(patient_id, current_user, db)
    db_patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    update_data = patient_update.model_dump(exclude_unset=True) if hasattr(patient_update, 'model_dump') else patient_update.dict(exclude_unset=True)
    
    # Check duplicates if name/date changed
    new_nom = update_data.get('nom', db_patient.nom).upper().strip()
    new_prenom = update_data.get('prenom', db_patient.prenom).capitalize().strip()
    new_date = update_data.get('date_naissance', db_patient.date_naissance)
    
    if (new_nom != db_patient.nom or 
        new_prenom != db_patient.prenom or 
        new_date != db_patient.date_naissance):
        existing = check_duplicate_patient(db, new_nom, new_prenom, new_date, exclude_id=patient_id)
        if existing:
            raise HTTPException(status_code=409, detail="Un autre patient avec le même nom et date de naissance existe déjà")

    # Update normalization
    if 'nom' in update_data: update_data['nom'] = update_data['nom'].upper().strip()
    if 'prenom' in update_data: update_data['prenom'] = update_data['prenom'].capitalize().strip()
    
    for key, value in update_data.items():
        setattr(db_patient, key, value)
    
    # Audit log
    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=current_user.get_employer_id(),
        action="UPDATE",
        resource_type="Patient",
        resource_id=str(patient_id),
        details=f"Mise a jour des donnees du patient {patient_id}. Champs modifies: {list(update_data.keys())}"
    )
    
    db.commit()
    db.refresh(db_patient)
    return db_patient

# --- GÉNÉRATION RAPPORTS (COMPATIBILITÉ) ---

@router.get("/{patient_id}/cephalo-validation")
def validate_cephalo_before_pdf(
    patient_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("cephalo")),
):
    """Pré-valide les mesures céphalo avant génération PDF. Retourne fatals + warnings."""
    assert_patient_access(patient_id, current_user, db)
    last_analysis = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.patient_id == patient_id
    ).order_by(models.CephaloAnalysis.id.desc()).first()
    if not last_analysis:
        raise HTTPException(status_code=404, detail="Aucune analyse céphalométrique trouvée")

    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    result = cephalo_consistency_validator.validate(last_analysis.angles_data or {})
    return result.to_dict()


@router.post("/{patient_id}/pdf")
def generate_cephalo_pdf(
    patient_id: int, 
    req: schemas.CephaloPDFRequest, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(require_permission("cephalo"))
):
    """Génération du rapport céphalo PDF (Route de compatibilité Ghost Elite)."""
    from backend.routers.documents import doc_factory
    from fastapi.responses import FileResponse
    
    assert_patient_access(patient_id, current_user, db)
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    
    last_analysis = db.query(models.CephaloAnalysis).filter(
        models.CephaloAnalysis.patient_id == patient_id
    ).order_by(models.CephaloAnalysis.id.desc()).first()
    
    if not last_analysis:
        raise HTTPException(status_code=404, detail="Aucune analyse céphalométrique trouvée pour ce patient")

    from backend.services.cephalo_consistency_validator import cephalo_consistency_validator
    validation = cephalo_consistency_validator.validate(last_analysis.angles_data or {})
    # Bloquer uniquement l'archivage officiel — le brouillon (archive=False) reste accessible
    if req.archive and not validation.is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Archivage refusé : incohérences bloquantes dans les mesures céphalo.",
                "fatals": validation.fatals,
                "warnings": validation.warnings,
            },
        )

    analysis_data = {
        "id": last_analysis.id,
        "image_path": last_analysis.image_original_path,
        "results": last_analysis.angles_data or {},
        "landmarks": last_analysis.landmarks_data,
        "_is_pre_bilan": not req.archive,
        "_validation_warnings": validation.warnings
    }

    if req.ai_diagnostic:
        analysis_data["results"]["ai_diagnostic"] = req.ai_diagnostic
    if req.clinical_data:
        analysis_data["results"]["clinical_data"] = req.clinical_data.model_dump() if hasattr(req.clinical_data, 'model_dump') else req.clinical_data

    pdf_path = doc_factory.create_cephalo_report(patient, analysis_data, db=db, user_id=current_user.id)
    
    if req.archive:
        from backend.services.archive_service import ArchiveService
        from backend.schemas import ConflictResolution
        
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            
        archive_svc = ArchiveService(db)
        try:
            archive_svc.archive_document(
                patient_id=patient_id,
                file_content=pdf_bytes,
                filename=os.path.basename(pdf_path),
                doc_type=models.DocumentType.RAPPORT_CEPHALO,
                uploaded_by_id=current_user.id,
                title="Bilan Céphalométrique et Plan ODF",
                clinical_data=analysis_data.get("results", {}).get("clinical_data", {}),
                on_conflict=ConflictResolution.CREATE_VERSION
            )
        except Exception as e:
            logger.warning("Archivage du rapport céphalo ignoré (doublon ou erreur) : %s", e)
            
    return FileResponse(path=pdf_path, filename=os.path.basename(pdf_path), media_type='application/pdf')

# --- MASTER PLAN CLINIQUE ---

@router.get("/{patient_id}/master-plan", response_model=Optional[schemas.TreatmentMasterPlanOut])
def get_master_plan(patient_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("clinical"))):
    assert_patient_access(patient_id, current_user, db)
    plan = db.query(models.TreatmentMasterPlan).filter(models.TreatmentMasterPlan.patient_id == patient_id).first()
    return plan

@router.put("/{patient_id}/master-plan", response_model=schemas.TreatmentMasterPlanOut)
def update_master_plan(patient_id: int, steps: List[schemas.TreatmentPlanStepCreate], db: Session = Depends(database.get_db), current_user: models.User = Depends(require_permission("clinical"))):
    assert_patient_access(patient_id, current_user, db)
    plan = db.query(models.TreatmentMasterPlan).filter(models.TreatmentMasterPlan.patient_id == patient_id).first()
    if not plan:
        plan = models.TreatmentMasterPlan(patient_id=patient_id)
        db.add(plan)
        db.flush()
    else:
        db.query(models.TreatmentPlanStep).filter(models.TreatmentPlanStep.plan_id == plan.id).delete()
        
    for i, step_data in enumerate(steps):
        step = models.TreatmentPlanStep(
            plan_id=plan.id,
            title=step_data.title,
            assistant=step_data.assistant,
            status=step_data.status,
            date_str=step_data.date_str,
            order_index=i
        )
        db.add(step)
        
    db.commit()
    db.refresh(plan)
    return plan


# --- SUPPRESSION ---

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """Archive un patient (soft-delete — jamais de perte de vraie donnée patient).
    Seul Dentiste/Proprio ou Admin. Masqué des points d'entrée normaux (liste,
    doublon, GET détail) ; les données restent conservées en base."""
    from backend.services.audit_service import audit_service

    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient or patient.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Patient introuvable")

    assert_patient_access(patient_id, current_user, db)

    if not is_superadmin_user(current_user) and (not current_user.role or current_user.role.value not in ["DENTISTE", "ADMIN"]):
        raise HTTPException(status_code=403, detail="Vous n'avez pas l'autorisation de supprimer un patient")

    try:
        # Audit log before archiving
        audit_service.log(
            db=db,
            user_id=current_user.id,
            employer_id=current_user.get_employer_id(),
            action="DELETE",
            resource_type="Patient",
            resource_id=str(patient_id),
            details=f"Archivage (soft-delete) du patient {patient.nom} {patient.prenom}"
        )

        patient.deleted_at = datetime.now()
        patient.deleted_by = current_user.id
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression: {str(e)}")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- IMPORT CSV ---

_CSV_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"]

def _parse_date(value: str) -> Optional[datetime]:
    for fmt in _CSV_DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


@router.post("/import-csv", summary="Importer des patients depuis un fichier CSV")
async def import_patients_csv(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients")),
):
    """
    Colonnes attendues (case-insensitive, ordre libre) :
    nom, prenom, date_naissance, telephone, email, assurance
    Seuls nom + prenom + date_naissance sont obligatoires.
    Les doublons (même nom+prenom+date_naissance) sont ignorés (skipped).
    """
    employer_id = current_user.get_employer_id()

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    # Auto-detect delimiter
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
    except csv.Error:
        dialect = csv.excel  # default

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    # Normalise headers
    if reader.fieldnames is None:
        raise HTTPException(status_code=422, detail="Fichier CSV vide ou sans en-têtes")

    headers = {h.strip().lower(): h for h in reader.fieldnames if h}

    created = 0
    skipped_duplicates = 0
    errors: list[dict] = []

    for row_num, row in enumerate(reader, start=2):
        nom_raw = row.get(headers.get("nom", ""), "").strip()
        prenom_raw = row.get(headers.get("prenom", ""), "").strip()
        dob_raw = row.get(headers.get("date_naissance", ""), "").strip()

        if not nom_raw or not prenom_raw or not dob_raw:
            errors.append({"row": row_num, "reason": "Champs obligatoires manquants (nom, prenom, date_naissance)"})
            continue

        dob = _parse_date(dob_raw)
        if dob is None:
            errors.append({"row": row_num, "reason": f"Format de date invalide : {dob_raw}"})
            continue

        nom = nom_raw.upper()
        prenom = prenom_raw.capitalize()

        if check_duplicate_patient(db, nom, prenom, dob):
            skipped_duplicates += 1
            continue

        telephone = row.get(headers.get("telephone", ""), "").strip() or None
        email = row.get(headers.get("email", ""), "").strip() or None
        assurance = row.get(headers.get("assurance", ""), "").strip() or None
        sexe_raw = row.get(headers.get("sexe", ""), "").strip().upper()
        sexe = sexe_raw if sexe_raw in ("M", "F") else "M"

        db_patient = models.Patient(
            nom=nom,
            prenom=prenom,
            date_naissance=dob,
            sexe=sexe,
            telephone=telephone,
            email=email,
            assurance=assurance,
            employer_id=employer_id,
            numero_dossier=generate_next_dossier_number(db, employer_id),
        )
        db.add(db_patient)
        db.flush()
        db.add(models.DossierClinique(patient_id=db_patient.id, is_ortho_active=False))
        created += 1

    db.commit()

    audit_service.log(
        db=db,
        user_id=current_user.id,
        employer_id=employer_id,
        action="IMPORT",
        resource_type="Patient",
        resource_id="bulk",
        details=f"Import CSV : {created} créés, {skipped_duplicates} doublons ignorés, {len(errors)} erreurs",
    )

    return {"created": created, "skipped_duplicates": skipped_duplicates, "errors": errors}


