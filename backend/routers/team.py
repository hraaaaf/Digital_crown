"""
Routes de gestion d'équipe (Sous-comptes assistantes).
RBAC : Seul un DENTISTE ou ADMIN peut créer/modifier/supprimer des sous-comptes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import models, schemas, database
from backend.routers.auth import get_current_user
from backend.security import get_password_hash

router = APIRouter(prefix="/team", tags=["Team Management"])


# --- DÉPENDANCE RBAC : Praticien uniquement ---

def require_employer(current_user: models.User = Depends(get_current_user)) -> models.User:
    """Bloque l'accès aux sous-comptes (SECRETAIRE) pour les opérations de gestion d'équipe."""
    if current_user.role == models.UserRole.SECRETAIRE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au praticien principal."
        )
    return current_user


# --- CRUD SOUS-COMPTES ---

@router.get("/", response_model=List[schemas.TeamMemberOut])
def list_team_members(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_employer)
):
    """Liste les membres de l'équipe rattachés au praticien connecté."""
    members = db.query(models.User).filter(
        models.User.employer_id == current_user.id
    ).order_by(models.User.created_at.desc()).all()
    return members


@router.post("/", response_model=schemas.TeamMemberOut, status_code=status.HTTP_201_CREATED)
def create_team_member(
    member: schemas.TeamMemberCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_employer)
):
    """Crée un sous-compte assistante rattaché au praticien connecté."""
    # Anti-doublon email
    existing = db.query(models.User).filter(models.User.email == member.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"L'email '{member.email}' est déjà utilisé par un autre compte."
        )

    # Permissions par défaut pour une assistante (SECRETAIRE)
    default_permissions = {
        "agenda": True,
        "patients": True,
        "prescriptions": False,
        "accounting": False,
        "panoramic": False,
        "cephalo": False,
        "settings": False
    }
    user_perms = member.permissions if member.permissions is not None else default_permissions

    new_user = models.User(
        email=member.email,
        hashed_password=get_password_hash(member.password),
        role=models.UserRole.SECRETAIRE,
        nom_complet=member.nom_complet,
        telephone_mobile=member.telephone_mobile,
        employer_id=current_user.id,
        is_active=True,
        permissions=user_perms
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/{member_id}", response_model=schemas.TeamMemberOut)
def update_team_member(
    member_id: int,
    updates: schemas.TeamMemberUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_employer)
):
    """Met à jour un sous-compte existant (nom, email, statut, mot de passe, permissions)."""
    member = db.query(models.User).filter(
        models.User.id == member_id,
        models.User.employer_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable dans votre équipe.")

    if updates.nom_complet is not None:
        member.nom_complet = updates.nom_complet
    if updates.email is not None:
        # Vérification unicité
        conflict = db.query(models.User).filter(
            models.User.email == updates.email,
            models.User.id != member_id
        ).first()
        if conflict:
            raise HTTPException(status_code=409, detail=f"L'email '{updates.email}' est déjà utilisé.")
        member.email = updates.email
    if updates.telephone_mobile is not None:
        member.telephone_mobile = updates.telephone_mobile
    if updates.is_active is not None:
        member.is_active = updates.is_active
    if updates.new_password is not None:
        member.hashed_password = get_password_hash(updates.new_password)
    if updates.permissions is not None:
        member.permissions = updates.permissions

    db.commit()
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team_member(
    member_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(require_employer)
):
    """Supprime définitivement un sous-compte de l'équipe."""
    member = db.query(models.User).filter(
        models.User.id == member_id,
        models.User.employer_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Membre introuvable dans votre équipe.")

    db.delete(member)
    db.commit()
