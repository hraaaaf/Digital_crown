from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from backend import models, database
from backend.routers.auth import require_permission

router = APIRouter()


def _serialize(item: models.StockItem) -> dict:
    return {
        "id":            item.id,
        "nom":           item.nom,
        "categorie":     item.categorie.value,
        "quantite":      item.quantite,
        "seuil_alerte":  item.seuil_alerte,
        "unite":         item.unite,
        "prix_unitaire": item.prix_unitaire,
        "fournisseur":   item.fournisseur,
        "notes":         item.notes,
        "alerte":        item.quantite <= item.seuil_alerte,
        "created_at":    item.created_at.isoformat() if item.created_at else None,
        "updated_at":    item.updated_at.isoformat() if item.updated_at else None,
    }


class StockItemCreate(BaseModel):
    nom: str
    categorie: str
    quantite: float = 0.0
    seuil_alerte: float = 5.0
    unite: str = "unité"
    prix_unitaire: Optional[float] = None
    fournisseur: Optional[str] = None
    notes: Optional[str] = None


@router.get("/items")
def get_stock_items(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    items = (
        db.query(models.StockItem)
        .filter(models.StockItem.employer_id == employer_id)
        .order_by(models.StockItem.categorie, models.StockItem.nom)
        .all()
    )
    return [_serialize(i) for i in items]


@router.get("/alerts")
def get_stock_alerts(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    items = (
        db.query(models.StockItem)
        .filter(
            models.StockItem.employer_id == employer_id,
            models.StockItem.quantite <= models.StockItem.seuil_alerte,
        )
        .order_by(models.StockItem.quantite)
        .all()
    )
    return {"count": len(items), "items": [_serialize(i) for i in items]}


@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_stock_item(
    req: StockItemCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    try:
        cat = models.StockCategorie(req.categorie)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Catégorie invalide : {req.categorie}")
    item = models.StockItem(
        employer_id=employer_id,
        nom=req.nom,
        categorie=cat,
        quantite=req.quantite,
        seuil_alerte=req.seuil_alerte,
        unite=req.unite,
        prix_unitaire=req.prix_unitaire,
        fournisseur=req.fournisseur,
        notes=req.notes,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _serialize(item)


@router.patch("/items/{item_id}")
def update_stock_item(
    item_id: int,
    req: Dict[str, Any],
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    item = (
        db.query(models.StockItem)
        .filter(models.StockItem.id == item_id, models.StockItem.employer_id == employer_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Article introuvable")
    allowed = {"nom", "categorie", "quantite", "seuil_alerte", "unite", "prix_unitaire", "fournisseur", "notes"}
    for field, value in req.items():
        if field not in allowed:
            continue
        if field == "categorie":
            try:
                value = models.StockCategorie(value)
            except ValueError:
                raise HTTPException(status_code=422, detail=f"Catégorie invalide : {value}")
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return _serialize(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock_item(
    item_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_permission("patients"))
):
    employer_id = current_user.get_employer_id()
    item = (
        db.query(models.StockItem)
        .filter(models.StockItem.id == item_id, models.StockItem.employer_id == employer_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Article introuvable")
    db.delete(item)
    db.commit()
