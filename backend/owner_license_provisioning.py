from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from backend import database, models
from backend.config import settings
from backend.license_issuer import LicenseIssuerUnavailable, issue_license
from backend.license_security import LicenseSecurityError, VerifiedLicense
from backend.platform_access import is_platform_superadmin
from backend.services.license_service import LicenseService


class OwnerProvisioningError(RuntimeError):
    """OWNER provisioning failed closed before local authority was changed."""


def _clinic_id(cabinet: models.CabinetConfig) -> str:
    value = cabinet.clinic_id or cabinet.public_id
    if not value:
        raise OwnerProvisioningError("Owner cabinet has no stable clinic/public id.")
    return str(value)


def _resolve_owner(
    db: Session,
    *,
    owner_user_id: int,
) -> tuple[models.User, models.CabinetConfig, str]:
    if not bool(getattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)):
        raise OwnerProvisioningError("OWNER provisioning is control-plane-only.")

    configured_owner_id = int(getattr(settings, "SUPERADMIN_USER_ID", 0) or 0)
    if configured_owner_id <= 0:
        raise OwnerProvisioningError("SUPERADMIN_USER_ID is not provisioned.")
    if int(owner_user_id) != configured_owner_id:
        raise OwnerProvisioningError(
            "Explicit owner id does not match immutable SUPERADMIN_USER_ID."
        )

    owner = db.query(models.User).filter(models.User.id == configured_owner_id).first()
    if owner is None:
        raise OwnerProvisioningError("Configured owner account does not exist.")
    if not is_platform_superadmin(owner):
        raise OwnerProvisioningError("Configured owner account is not an active platform owner.")

    cabinet = (
        db.query(models.CabinetConfig)
        .filter(models.CabinetConfig.owner_id == owner.id)
        .first()
    )
    if cabinet is None:
        raise OwnerProvisioningError("Owner cabinet is not configured.")

    return owner, cabinet, _clinic_id(cabinet)


def _assert_owner_token(
    verified: VerifiedLicense,
    *,
    owner_user_id: int,
) -> None:
    if verified.license_type != "OWNER":
        raise OwnerProvisioningError("Issued token is not OWNER.")
    if verified.status != "ACTIVE":
        raise OwnerProvisioningError("Issued OWNER token is not ACTIVE.")
    if verified.subject_user_id != int(owner_user_id):
        raise OwnerProvisioningError("Issued OWNER subject does not match SUPERADMIN_USER_ID.")
    if verified.expires_at is not None:
        raise OwnerProvisioningError("OWNER token unexpectedly expires.")
    if verified.claims.get("feature_set") != models.SubscriptionPlan.ELITE.value:
        raise OwnerProvisioningError("OWNER token does not carry ELITE entitlement.")
    if verified.claims.get("max_devices") is not None:
        raise OwnerProvisioningError("OWNER token unexpectedly limits devices.")


async def provision_owner_license(
    db: Session,
    *,
    owner_user_id: int,
    apply: bool = False,
) -> dict[str, Any]:
    """Provision the immutable OWNER entitlement without exposing a network route.

    Dry-run is the default. `apply=True` is required before Firebase or the local
    informational mirror is changed. The private signing key remains environment-
    only on the dedicated control plane.
    """
    owner, cabinet, clinic_id = _resolve_owner(db, owner_user_id=owner_user_id)
    service = LicenseService()

    if apply:
        current = await service.validate_license_with_expiry(clinic_id)
        if (
            current.get("active") is True
            and current.get("source") == "firebase"
            and current.get("license_type") == "OWNER"
            and current.get("feature_set") == models.SubscriptionPlan.ELITE.value
            and current.get("expiration_date") is None
        ):
            owner.is_licensed = True
            owner.subscription_plan = models.SubscriptionPlan.ELITE.value
            owner.license_expires_at = None
            db.commit()
            return {
                "ok": True,
                "applied": False,
                "already_provisioned": True,
                "owner_user_id": owner.id,
                "cabinet_id": clinic_id,
                "license_id": current.get("license_id"),
                "feature_set": models.SubscriptionPlan.ELITE.value,
                "source": "firebase",
            }

    try:
        signed_license = issue_license(
            cabinet_id=clinic_id,
            license_type="OWNER",
            created_by_user_id=owner.id,
            expires_at=None,
            release_channel="stable",
            feature_set=models.SubscriptionPlan.ELITE.value,
            max_devices=None,
            status="ACTIVE",
            subject_user_id=owner.id,
        )
        verified = LicenseService._verify_signed_license(
            signed_license,
            clinic_id,
            datetime.now(timezone.utc),
        )
    except (LicenseIssuerUnavailable, LicenseSecurityError) as exc:
        raise OwnerProvisioningError(
            "OWNER signing or local trust verification is not provisioned."
        ) from exc

    _assert_owner_token(verified, owner_user_id=owner.id)

    result: dict[str, Any] = {
        "ok": True,
        "applied": False,
        "already_provisioned": False,
        "owner_user_id": owner.id,
        "cabinet_id": clinic_id,
        "license_id": verified.license_id,
        "feature_set": models.SubscriptionPlan.ELITE.value,
        "source": "dry-run",
    }
    if not apply:
        return result

    if not await service.write_signed_license(
        public_id=clinic_id,
        signed_license=signed_license,
    ):
        raise OwnerProvisioningError("Signed OWNER token was not persisted to Firebase.")

    read_back = await service.validate_license_with_expiry(clinic_id)
    if not (
        read_back.get("active") is True
        and read_back.get("source") == "firebase"
        and read_back.get("license_type") == "OWNER"
        and read_back.get("feature_set") == models.SubscriptionPlan.ELITE.value
        and read_back.get("expiration_date") is None
        and read_back.get("license_id") == verified.license_id
    ):
        raise OwnerProvisioningError(
            "Firebase OWNER read-back did not match the signed token; local mirror unchanged."
        )

    owner.is_licensed = True
    owner.subscription_plan = models.SubscriptionPlan.ELITE.value
    owner.license_expires_at = None
    db.add(
        models.LicenseHistory(
            user_id=owner.id,
            admin_id=owner.id,
            action="OWNER_ENTITLEMENT_ISSUED_SIGNED",
            duration=None,
        )
    )
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise OwnerProvisioningError(
            "Signed OWNER is persisted but local mirror/audit commit failed; investigate before retry."
        ) from exc

    result.update({"applied": True, "source": "firebase"})
    return result


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provision Digital Crown SEC-1 OWNER entitlement on the dedicated control plane."
    )
    parser.add_argument(
        "--owner-user-id",
        type=int,
        required=True,
        help="Must exactly match configured SUPERADMIN_USER_ID.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist the signed OWNER token. Without this flag the command is dry-run only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db = database.SessionLocal()
    try:
        result = asyncio.run(
            provision_owner_license(
                db,
                owner_user_id=args.owner_user_id,
                apply=args.apply,
            )
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except OwnerProvisioningError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
