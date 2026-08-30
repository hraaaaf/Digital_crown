"""Least-privilege platform operator management for the dedicated control plane."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from backend import database, models
from backend.config import settings
from backend.platform_access import (
    PLATFORM_LICENSE_PERMISSIONS,
    has_platform_permission,
    is_platform_superadmin,
)
from backend.platform_step_up import enforce_platform_step_up_for_mutation
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/platform-admins", tags=["SuperAdmin Operators"])


class PlatformPermissionsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    permissions: dict[str, bool] = Field(default_factory=dict)

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, value: dict[str, bool]) -> dict[str, bool]:
        unknown = sorted(set(value) - set(PLATFORM_LICENSE_PERMISSIONS))
        if unknown:
            raise ValueError(f"Permissions plateforme inconnues : {unknown}")
        return {key: bool(enabled) for key, enabled in value.items()}


class PlatformOperatorEnabledPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


def _require(permission: str):
    def dependency(
        request: Request,
        db: Session = Depends(database.get_db),
        current_user: models.User = Depends(get_current_user),
    ) -> models.User:
        if not has_platform_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail="Accès refusé. Permission plateforme insuffisante.",
            )
        enforce_platform_step_up_for_mutation(
            request,
            current_user=current_user,
            db=db,
        )
        return current_user

    return dependency


def _true_permissions(user: models.User) -> set[str]:
    if is_platform_superadmin(user):
        return set(PLATFORM_LICENSE_PERMISSIONS)
    raw = user.permissions if isinstance(user.permissions, dict) else {}
    return {
        permission
        for permission in PLATFORM_LICENSE_PERMISSIONS
        if raw.get(permission) is True
    }


def _assert_no_privilege_escalation(actor: models.User, requested: dict[str, bool]) -> None:
    if is_platform_superadmin(actor):
        return
    requested_true = {key for key, enabled in requested.items() if enabled}
    if not requested_true.issubset(_true_permissions(actor)):
        raise HTTPException(
            status_code=403,
            detail="Un opérateur ne peut déléguer que ses propres permissions plateforme.",
        )


def _owner_id() -> int:
    return int(getattr(settings, "SUPERADMIN_USER_ID", 0) or 0)


def _target(db: Session, user_id: int) -> models.User:
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return user


def _assert_platform_only_account(db: Session, user: models.User) -> None:
    if user.employer_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Un compte rattaché à un cabinet ne peut pas devenir opérateur plateforme.",
        )
    cabinet = db.query(models.CabinetConfig).filter(
        models.CabinetConfig.owner_id == user.id
    ).first()
    if cabinet is not None:
        raise HTTPException(
            status_code=409,
            detail="Un propriétaire de cabinet ne peut pas devenir opérateur plateforme.",
        )


def _assert_mutable_operator_target(user: models.User) -> None:
    if user.id == _owner_id():
        raise HTTPException(
            status_code=403,
            detail="Le SuperAdmin immuable ne peut pas être modifié via la délégation opérateur.",
        )


def _audit(
    db: Session,
    *,
    actor_id: int,
    action: str,
    target_id: int,
    details: str,
    severity: str = "WARNING",
) -> None:
    db.add(
        models.AuditLog(
            user_id=actor_id,
            employer_id=None,
            action=action,
            resource_type="PlatformOperator",
            resource_id=str(target_id),
            severity=severity,
            details=details,
        )
    )


def _serialize(user: models.User) -> dict:
    permissions = {
        permission: True
        for permission in sorted(_true_permissions(user))
    }
    return {
        "id": user.id,
        "email": user.email,
        "nom_complet": user.nom_complet,
        "is_active": user.is_active,
        "is_suspended": user.is_suspended,
        "is_owner": user.id == _owner_id(),
        "permissions": permissions,
    }


@router.get("")
def list_platform_operators(
    db: Session = Depends(database.get_db),
    actor: models.User = Depends(_require("admin.read")),
):
    users = db.query(models.User).filter(models.User.employer_id.is_(None)).all()
    result = []
    for user in users:
        if user.id == _owner_id() or _true_permissions(user):
            result.append(_serialize(user))
    return sorted(result, key=lambda row: (not row["is_owner"], row["id"]))


@router.post("/{user_id}")
def create_platform_operator(
    user_id: int,
    payload: PlatformPermissionsPayload,
    db: Session = Depends(database.get_db),
    actor: models.User = Depends(_require("admin.create")),
):
    target = _target(db, user_id)
    _assert_mutable_operator_target(target)
    _assert_platform_only_account(db, target)
    if not target.is_active or target.is_archived or target.is_suspended:
        raise HTTPException(
            status_code=409,
            detail="Le compte plateforme cible doit être actif et non suspendu.",
        )
    if _true_permissions(target):
        raise HTTPException(status_code=409, detail="Cet opérateur plateforme existe déjà.")
    if not any(payload.permissions.values()):
        raise HTTPException(status_code=400, detail="Au moins une permission plateforme est requise.")
    _assert_no_privilege_escalation(actor, payload.permissions)

    target.permissions = dict(payload.permissions)
    _audit(
        db,
        actor_id=actor.id,
        action="SUPERADMIN_OPERATOR_CREATE",
        target_id=target.id,
        details="permissions=" + ",".join(sorted(_true_permissions(target))),
        severity="CRITICAL",
    )
    db.commit()
    db.refresh(target)
    return _serialize(target)


@router.patch("/{user_id}/permissions")
def update_platform_operator_permissions(
    user_id: int,
    payload: PlatformPermissionsPayload,
    db: Session = Depends(database.get_db),
    actor: models.User = Depends(_require("admin.update_permissions")),
):
    target = _target(db, user_id)
    _assert_mutable_operator_target(target)
    _assert_platform_only_account(db, target)
    if not _true_permissions(target):
        raise HTTPException(status_code=404, detail="Opérateur plateforme introuvable.")
    _assert_no_privilege_escalation(actor, payload.permissions)

    before = sorted(_true_permissions(target))
    target.permissions = dict(payload.permissions)
    after = sorted(_true_permissions(target))
    _audit(
        db,
        actor_id=actor.id,
        action="SUPERADMIN_OPERATOR_PERMISSIONS_UPDATE",
        target_id=target.id,
        details=f"from={','.join(before)};to={','.join(after)}",
        severity="CRITICAL",
    )
    db.commit()
    db.refresh(target)
    return _serialize(target)


@router.patch("/{user_id}/enabled")
def set_platform_operator_enabled(
    user_id: int,
    payload: PlatformOperatorEnabledPayload,
    db: Session = Depends(database.get_db),
    actor: models.User = Depends(_require("admin.disable")),
):
    target = _target(db, user_id)
    _assert_mutable_operator_target(target)
    _assert_platform_only_account(db, target)
    if not _true_permissions(target):
        raise HTTPException(status_code=404, detail="Opérateur plateforme introuvable.")

    target.is_active = payload.enabled
    _audit(
        db,
        actor_id=actor.id,
        action="SUPERADMIN_OPERATOR_ENABLE" if payload.enabled else "SUPERADMIN_OPERATOR_DISABLE",
        target_id=target.id,
        details=f"enabled={str(payload.enabled).lower()}",
        severity="CRITICAL",
    )
    db.commit()
    db.refresh(target)
    return _serialize(target)
