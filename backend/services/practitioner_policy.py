"""Shared practitioner eligibility policy for multi-practitioner clinical attribution."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend import models


def is_assignable_practitioner(user: models.User, employer_id: int) -> bool:
    """Return True only for an active, approved practitioner in the same cabinet."""
    if not user.is_active or user.approval_status != models.ApprovalStatus.APPROVED.value:
        return False
    if user.id == employer_id:
        return user.role in (models.UserRole.DENTISTE, models.UserRole.ADMIN)
    return user.employer_id == employer_id and user.role == models.UserRole.DENTISTE


def validate_practitioner(db: Session, employer_id: int, practitioner_id: int) -> models.User:
    """Resolve a practitioner id fail-closed inside the current cabinet."""
    practitioner = db.query(models.User).filter(models.User.id == int(practitioner_id)).first()
    if not practitioner or not is_assignable_practitioner(practitioner, employer_id):
        raise HTTPException(status_code=403, detail="Praticien non assignable dans ce cabinet")
    return practitioner


def resolve_document_author(
    db: Session,
    current_user: models.User,
    requested_practitioner_id: Optional[int],
) -> models.User:
    """Resolve the truthful clinical author while preserving the authenticated actor.

    Backward compatibility is intentionally narrow: an authenticated practitioner may
    omit the author and remains the author. A non-practitioner actor must select an
    explicit practitioner; silently attributing the document to the cabinet owner would
    create false clinical provenance.
    """
    employer_id = current_user.get_employer_id()
    if requested_practitioner_id is not None:
        return validate_practitioner(db, employer_id, requested_practitioner_id)
    if is_assignable_practitioner(current_user, employer_id):
        return current_user
    raise HTTPException(
        status_code=422,
        detail="Auteur praticien requis pour générer ce document",
    )


def practitioner_payload(user: models.User) -> dict:
    return {
        "id": user.id,
        "name": user.nom_complet or user.email or f"Praticien {user.id}",
        "role": getattr(user.role, "value", user.role),
    }
