from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend import database, models
from backend.config import settings
from backend.license_issuer import LicenseIssuerUnavailable, issue_license
from backend.license_security import LicenseSecurityError
from backend.platform_access import is_platform_superadmin
from backend.services.license_service import LicenseService


class LegacyLicenseMigrationError(RuntimeError):
    """Legacy licence migration could not proceed safely."""


def _as_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str) and value.strip():
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise LegacyLicenseMigrationError("Invalid legacy expiration timestamp.") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise LegacyLicenseMigrationError("Unsupported legacy expiration value.")


def _require_control_plane_issuer(db: Session, issuer_user_id: int) -> models.User:
    if not bool(getattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)):
        raise LegacyLicenseMigrationError("Legacy migration is control-plane-only.")
    configured_owner_id = int(getattr(settings, "SUPERADMIN_USER_ID", 0) or 0)
    if configured_owner_id <= 0:
        raise LegacyLicenseMigrationError("SUPERADMIN_USER_ID is not provisioned.")
    if int(issuer_user_id) != configured_owner_id:
        raise LegacyLicenseMigrationError(
            "Migration issuer must exactly match immutable SUPERADMIN_USER_ID."
        )
    issuer = db.query(models.User).filter(models.User.id == configured_owner_id).first()
    if issuer is None or not is_platform_superadmin(issuer):
        raise LegacyLicenseMigrationError("Configured migration issuer is not an active platform owner.")
    return issuer


def _fetch_license_documents(service: LicenseService) -> list[tuple[str, dict[str, Any]]]:
    if not service._db:
        raise LegacyLicenseMigrationError("Firebase control-plane connection is unavailable.")
    documents = []
    for document in service._db.collection("licenses").stream():
        data = document.to_dict() or {}
        documents.append((str(document.id), data if isinstance(data, dict) else {}))
    return documents


def _read_license_document(service: LicenseService, cabinet_id: str) -> dict[str, Any] | None:
    if not service._db:
        raise LegacyLicenseMigrationError("Firebase control-plane connection is unavailable.")
    document = service._db.collection("licenses").document(cabinet_id).get()
    if not document.exists:
        return None
    data = document.to_dict() or {}
    return data if isinstance(data, dict) else None


def _manifest_entry(
    manifest: Mapping[str, Any],
    cabinet_id: str,
) -> tuple[str, str, int] | None:
    raw = manifest.get(cabinet_id)
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise LegacyLicenseMigrationError(
            f"Manifest entry for {cabinet_id} must be an object."
        )
    license_type = str(raw.get("license_type") or "").upper()
    if license_type not in {"TRIAL", "PAID"}:
        raise LegacyLicenseMigrationError(
            f"Manifest entry for {cabinet_id} must use TRIAL or PAID; OWNER is provisioned separately."
        )
    feature_set = str(raw.get("feature_set") or "").upper()
    valid_feature_sets = {plan.value for plan in models.SubscriptionPlan}
    if feature_set not in valid_feature_sets:
        raise LegacyLicenseMigrationError(
            f"Manifest entry for {cabinet_id} requires feature_set GOLD, PREMIUM or ELITE."
        )
    max_devices = raw.get("max_devices")
    if isinstance(max_devices, bool) or not isinstance(max_devices, int) or max_devices < 1:
        raise LegacyLicenseMigrationError(
            f"Manifest entry for {cabinet_id} requires max_devices >= 1."
        )
    return license_type, feature_set, max_devices


def _find_local_owner(
    db: Session,
    cabinet_id: str,
) -> tuple[models.User, models.CabinetConfig] | None:
    cabinets = (
        db.query(models.CabinetConfig)
        .filter(
            or_(
                models.CabinetConfig.clinic_id == cabinet_id,
                models.CabinetConfig.public_id == cabinet_id,
            )
        )
        .all()
    )
    if len(cabinets) != 1:
        return None
    cabinet = cabinets[0]
    owner = db.query(models.User).filter(models.User.id == cabinet.owner_id).first()
    if owner is None:
        return None
    return owner, cabinet


async def migrate_legacy_licenses(
    db: Session,
    *,
    issuer_user_id: int,
    apply: bool = False,
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Replace unsigned Firebase licence records with signed SEC-1 entitlements.

    The old schema only carried `active` and `expiration_date`; it did not carry
    licence type, feature entitlement or device policy. Those missing security
    decisions are never inferred from mutable SQLite. `manifest` must explicitly
    provide TRIAL/PAID, feature_set and max_devices for every unsigned record
    before `apply=True` can write anything.

    OWNER is intentionally excluded and must be provisioned through the separate
    immutable OWNER workflow.
    """
    issuer = _require_control_plane_issuer(db, issuer_user_id)
    service = LicenseService()
    migration_manifest: Mapping[str, Any] = manifest or {}
    now = datetime.now(timezone.utc)

    report: dict[str, Any] = {
        "ok": True,
        "applied": False,
        "scanned": 0,
        "signed_skipped": 0,
        "planned": [],
        "manual": [],
        "migrated": [],
        "failed": [],
    }
    plans: list[dict[str, Any]] = []

    for cabinet_id, data in _fetch_license_documents(service):
        report["scanned"] += 1
        if isinstance(data.get("signed_license"), str) and data.get("signed_license"):
            report["signed_skipped"] += 1
            continue

        local = _find_local_owner(db, cabinet_id)
        if local is None:
            report["manual"].append(
                {"cabinet_id": cabinet_id, "reason": "local_cabinet_owner_not_unique_or_missing"}
            )
            continue
        owner, _cabinet = local

        active_raw = data.get("active")
        if not isinstance(active_raw, bool):
            report["manual"].append(
                {"cabinet_id": cabinet_id, "reason": "legacy_active_missing_or_invalid"}
            )
            continue
        active = active_raw

        try:
            expiration = _as_utc(data.get("expiration_date"))
        except LegacyLicenseMigrationError:
            report["manual"].append(
                {"cabinet_id": cabinet_id, "reason": "legacy_expiration_invalid"}
            )
            continue

        if active and expiration is None:
            report["manual"].append(
                {"cabinet_id": cabinet_id, "reason": "active_legacy_license_has_no_expiration"}
            )
            continue

        try:
            policy = _manifest_entry(migration_manifest, cabinet_id)
        except LegacyLicenseMigrationError as exc:
            report["manual"].append(
                {"cabinet_id": cabinet_id, "reason": str(exc)}
            )
            continue
        if policy is None:
            report["manual"].append(
                {"cabinet_id": cabinet_id, "reason": "migration_manifest_required"}
            )
            continue

        license_type, feature_set, max_devices = policy
        status = "ACTIVE" if active and expiration and expiration > now else "REVOKED"
        signed_expiration = expiration or now
        plan = {
            "cabinet_id": cabinet_id,
            "owner_id": owner.id,
            "license_type": license_type,
            "status": status,
            "expires_at": signed_expiration,
            "feature_set": feature_set,
            "max_devices": max_devices,
        }
        plans.append(plan)
        report["planned"].append(
            {
                "cabinet_id": cabinet_id,
                "license_type": license_type,
                "status": status,
                "expires_at": signed_expiration.isoformat(),
                "feature_set": feature_set,
                "max_devices": max_devices,
            }
        )

    if report["manual"]:
        report["ok"] = False
        return report
    if not apply:
        return report

    for plan in plans:
        try:
            signed_license = issue_license(
                cabinet_id=plan["cabinet_id"],
                license_type=plan["license_type"],
                created_by_user_id=issuer.id,
                expires_at=plan["expires_at"],
                release_channel="stable",
                feature_set=plan["feature_set"],
                max_devices=plan["max_devices"],
                status=plan["status"],
            )
            verified = LicenseService._verify_signed_license(
                signed_license,
                plan["cabinet_id"],
                datetime.now(timezone.utc),
                allow_inactive=plan["status"] != "ACTIVE",
            )
            if (
                verified.license_type != plan["license_type"]
                or verified.status != plan["status"]
                or verified.claims.get("feature_set") != plan["feature_set"]
                or verified.claims.get("max_devices") != plan["max_devices"]
            ):
                raise LegacyLicenseMigrationError("Issued migration token claims mismatch.")

            stored = await service.write_signed_license(
                public_id=plan["cabinet_id"],
                signed_license=signed_license,
            )
            if not stored:
                raise LegacyLicenseMigrationError("Signed migration token was not persisted.")

            read_back = _read_license_document(service, plan["cabinet_id"])
            if not read_back or read_back.get("signed_license") != signed_license:
                raise LegacyLicenseMigrationError("Firebase signed-token read-back mismatch.")
            read_back_verified = LicenseService._verify_signed_license(
                read_back["signed_license"],
                plan["cabinet_id"],
                datetime.now(timezone.utc),
                allow_inactive=plan["status"] != "ACTIVE",
            )
            if read_back_verified.license_id != verified.license_id:
                raise LegacyLicenseMigrationError("Firebase read-back license id mismatch.")

            report["migrated"].append(
                {
                    "cabinet_id": plan["cabinet_id"],
                    "license_id": verified.license_id,
                    "license_type": plan["license_type"],
                    "status": plan["status"],
                }
            )
        except (LicenseIssuerUnavailable, LicenseSecurityError, LegacyLicenseMigrationError) as exc:
            report["failed"].append(
                {"cabinet_id": plan["cabinet_id"], "reason": str(exc)}
            )
            report["ok"] = False
            report["applied"] = bool(report["migrated"])
            return report

    report["applied"] = bool(plans)
    return report


def _load_manifest(path: str | None) -> Mapping[str, Any]:
    if not path:
        return {}
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise LegacyLicenseMigrationError("Migration manifest must be a JSON object.")
    return value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run or apply SEC-1 migration of legacy unsigned Firebase licences."
    )
    parser.add_argument("--issuer-user-id", type=int, required=True)
    parser.add_argument(
        "--manifest",
        help='JSON map: {"cabinet-id": {"license_type": "PAID|TRIAL", "feature_set": "GOLD|PREMIUM|ELITE", "max_devices": 1}}',
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write signed replacements. Default is dry-run only.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    db = database.SessionLocal()
    try:
        manifest = _load_manifest(args.manifest)
        report = asyncio.run(
            migrate_legacy_licenses(
                db,
                issuer_user_id=args.issuer_user_id,
                apply=args.apply,
                manifest=manifest,
            )
        )
        print(json.dumps(report, sort_keys=True))
        return 0 if report.get("ok") else 3
    except (LegacyLicenseMigrationError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
