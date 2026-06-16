"""
CRUD admin pour les données cliniques versionnées en DB :
- Contre-indications (antécédent → molécules bannies)
- Pharmacopée marocaine (molécule → noms commerciaux, dosages)
- Protocoles par acte (procédure → molécules recommandées)

Accès réservé aux comptes disposant de la permission « clinical »
(praticien propriétaire ou sous-compte explicitement autorisé).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend import models, database
from backend.routers.auth import require_permission

router = APIRouter(tags=["Données Cliniques"])

# Garde unique : le propriétaire du cabinet passe toujours, un sous-compte doit
# avoir la permission « clinical » dans son JSON de droits (cf. has_permission).
_require_clinical = require_permission("clinical")


# ── SCHÉMAS ──────────────────────────────────────────────────────────────────

class ContraindicationIn(BaseModel):
    antecedent: str
    molecule: str

class ContraindicationOut(ContraindicationIn):
    id: int
    is_active: bool
    class Config: from_attributes = True


class DrugIn(BaseModel):
    molecule: str
    brand_names: List[str] = []
    dosages: List[str] = []
    form: Optional[str] = None

class DrugOut(DrugIn):
    id: int
    is_active: bool
    class Config: from_attributes = True


class ProtocolIn(BaseModel):
    procedure: str
    molecules: List[str] = []
    advice: Optional[str] = None

class ProtocolOut(ProtocolIn):
    id: int
    is_active: bool
    class Config: from_attributes = True


# ── CONTRE-INDICATIONS ────────────────────────────────────────────────────────

@router.get("/contraindications", response_model=List[ContraindicationOut],
    summary="Lister les contre-indications")
def list_contraindications(db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    return db.query(models.ClinicalContraindication).filter(
        models.ClinicalContraindication.is_active == True
    ).order_by(models.ClinicalContraindication.antecedent).all()


@router.post("/contraindications", response_model=ContraindicationOut, status_code=201,
    summary="Ajouter une contre-indication")
def create_contraindication(body: ContraindicationIn, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    ci = models.ClinicalContraindication(antecedent=body.antecedent.upper(), molecule=body.molecule.upper())
    db.add(ci); db.commit(); db.refresh(ci)
    return ci


@router.delete("/contraindications/{ci_id}", status_code=204,
    summary="Supprimer une contre-indication")
def delete_contraindication(ci_id: int, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    ci = db.query(models.ClinicalContraindication).filter(models.ClinicalContraindication.id == ci_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Contre-indication introuvable.")
    ci.is_active = False
    db.commit()


# ── PHARMACOPÉE ───────────────────────────────────────────────────────────────

@router.get("/drugs", response_model=List[DrugOut],
    summary="Lister la pharmacopée marocaine")
def list_drugs(db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    return db.query(models.ClinicalDrug).filter(
        models.ClinicalDrug.is_active == True
    ).order_by(models.ClinicalDrug.molecule).all()


@router.post("/drugs", response_model=DrugOut, status_code=201,
    summary="Ajouter un médicament")
def create_drug(body: DrugIn, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    existing = db.query(models.ClinicalDrug).filter(models.ClinicalDrug.molecule == body.molecule.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Molécule '{body.molecule}' déjà enregistrée.")
    drug = models.ClinicalDrug(molecule=body.molecule.upper(), brand_names=body.brand_names,
                                dosages=body.dosages, form=body.form)
    db.add(drug); db.commit(); db.refresh(drug)
    return drug


@router.put("/drugs/{drug_id}", response_model=DrugOut,
    summary="Mettre à jour un médicament")
def update_drug(drug_id: int, body: DrugIn, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    drug = db.query(models.ClinicalDrug).filter(models.ClinicalDrug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="Médicament introuvable.")
    drug.brand_names = body.brand_names
    drug.dosages = body.dosages
    drug.form = body.form
    db.commit(); db.refresh(drug)
    return drug


@router.delete("/drugs/{drug_id}", status_code=204,
    summary="Désactiver un médicament")
def delete_drug(drug_id: int, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    drug = db.query(models.ClinicalDrug).filter(models.ClinicalDrug.id == drug_id).first()
    if not drug:
        raise HTTPException(status_code=404, detail="Médicament introuvable.")
    drug.is_active = False
    db.commit()


# ── PROTOCOLES ────────────────────────────────────────────────────────────────

@router.get("/protocols", response_model=List[ProtocolOut],
    summary="Lister les protocoles par acte")
def list_protocols(db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    return db.query(models.ClinicalProtocolDB).filter(
        models.ClinicalProtocolDB.is_active == True
    ).order_by(models.ClinicalProtocolDB.procedure).all()


@router.post("/protocols", response_model=ProtocolOut, status_code=201,
    summary="Ajouter un protocole")
def create_protocol(body: ProtocolIn, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    existing = db.query(models.ClinicalProtocolDB).filter(models.ClinicalProtocolDB.procedure == body.procedure.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Protocole '{body.procedure}' déjà enregistré.")
    proto = models.ClinicalProtocolDB(procedure=body.procedure.upper(), molecules=body.molecules, advice=body.advice)
    db.add(proto); db.commit(); db.refresh(proto)
    return proto


@router.put("/protocols/{proto_id}", response_model=ProtocolOut,
    summary="Mettre à jour un protocole")
def update_protocol(proto_id: int, body: ProtocolIn, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    proto = db.query(models.ClinicalProtocolDB).filter(models.ClinicalProtocolDB.id == proto_id).first()
    if not proto:
        raise HTTPException(status_code=404, detail="Protocole introuvable.")
    proto.molecules = body.molecules
    proto.advice = body.advice
    db.commit(); db.refresh(proto)
    return proto


@router.delete("/protocols/{proto_id}", status_code=204,
    summary="Désactiver un protocole")
def delete_protocol(proto_id: int, db: Session = Depends(database.get_db), _=Depends(_require_clinical)):
    proto = db.query(models.ClinicalProtocolDB).filter(models.ClinicalProtocolDB.id == proto_id).first()
    if not proto:
        raise HTTPException(status_code=404, detail="Protocole introuvable.")
    proto.is_active = False
    db.commit()
