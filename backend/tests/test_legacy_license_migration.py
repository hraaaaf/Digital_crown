import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from backend import models
from backend.config import settings
from backend.license_security import VerifiedLicense
from backend.legacy_license_migration import (
    LegacyLicenseMigrationError,
    migrate_legacy_licenses,
)
from backend import legacy_license_migration as migration
from backend.services.license_service import LicenseService


def _create_user_and_cabinet(db, *, clinic_id: str, plan: str = models.SubscriptionPlan.GOLD.value):
    user = models.User(
        email=f"{clinic_id}@example.com",
        hashed_password="unused",
        role=models.UserRole.ADMIN,
        nom_complet="Legacy Migration",
        is_active=True,
        subscription_plan=plan,
    )
    db.add(user)
    db.flush()
    cabinet = models.CabinetConfig(
        owner_id=user.id,
        clinic_id=clinic_id,
        nom_cabinet=f"Cabinet {clinic_id}",
        nom_praticien="Dr Legacy",
    )
    db.add(cabinet)
    db.commit()
    db.refresh(user)
    return user


def _verified(plan, *, license_id="migrated-license"):
    return VerifiedLicense(
        claims={
            "license_id": license_id,
            "cabinet_id": plan["cabinet_id"],
            "license_type": plan["license_type"],
            "status": plan["status"],
            "expires_at": plan["expires_at"].isoformat(),
            "feature_set": plan["feature_set"],
            "max_devices": plan["max_devices"],
        },
        key_id="migration-k1",
    )


def test_migration_fails_closed_outside_control_plane(db, monkeypatch):
    issuer = _create_user_and_cabinet(db, clinic_id="issuer-clinic")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", issuer.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)

    with pytest.raises(LegacyLicenseMigrationError, match="control-plane-only"):
        asyncio.run(
            migrate_legacy_licenses(db, issuer_user_id=issuer.id, apply=False)
        )


def test_dry_run_refuses_ambiguous_legacy_records_before_any_write(db, monkeypatch):
    issuer = _create_user_and_cabinet(db, clinic_id="issuer-clinic")
    _create_user_and_cabinet(db, clinic_id="legacy-needs-manifest")
    _create_user_and_cabinet(db, clinic_id="legacy-perpetual")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", issuer.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)

    future = datetime.now(timezone.utc) + timedelta(days=30)
    docs = [
        ("already-signed", {"signed_license": "a.b.c", "active": True}),
        ("legacy-needs-manifest", {"active": True, "expiration_date": future}),
        ("legacy-perpetual", {"active": True, "expiration_date": None}),
        ("orphan", {"active": False, "expiration_date": None}),
    ]
    monkeypatch.setattr(migration, "_fetch_license_documents", lambda _service: docs)

    async def must_not_write(*_args, **_kwargs):
        raise AssertionError("preflight ambiguity must prevent all writes")

    monkeypatch.setattr(LicenseService, "write_signed_license", must_not_write)

    report = asyncio.run(
        migrate_legacy_licenses(
            db,
            issuer_user_id=issuer.id,
            apply=True,
            manifest={},
        )
    )

    assert report["ok"] is False
    assert report["applied"] is False
    assert report["signed_skipped"] == 1
    reasons = {entry["cabinet_id"]: entry["reason"] for entry in report["manual"]}
    assert reasons["legacy-needs-manifest"] == "migration_manifest_required"
    assert reasons["legacy-perpetual"] == "active_legacy_license_has_no_expiration"
    assert reasons["orphan"] == "local_cabinet_owner_not_unique_or_missing"


def test_invalid_legacy_active_type_is_never_coerced_true(db, monkeypatch):
    issuer = _create_user_and_cabinet(db, clinic_id="issuer-clinic")
    _create_user_and_cabinet(db, clinic_id="legacy-string-active")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", issuer.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(
        migration,
        "_fetch_license_documents",
        lambda _service: [
            (
                "legacy-string-active",
                {
                    "active": "false",
                    "expiration_date": datetime.now(timezone.utc) + timedelta(days=30),
                },
            )
        ],
    )

    async def must_not_write(*_args, **_kwargs):
        raise AssertionError("malformed active value must prevent all writes")

    monkeypatch.setattr(LicenseService, "write_signed_license", must_not_write)

    report = asyncio.run(
        migrate_legacy_licenses(
            db,
            issuer_user_id=issuer.id,
            apply=True,
            manifest={
                "legacy-string-active": {
                    "license_type": "PAID",
                    "feature_set": "GOLD",
                    "max_devices": 1,
                }
            },
        )
    )

    assert report["ok"] is False
    assert report["applied"] is False
    assert report["planned"] == []
    assert report["manual"] == [
        {
            "cabinet_id": "legacy-string-active",
            "reason": "legacy_active_missing_or_invalid",
        }
    ]


def test_apply_migrates_active_and_revoked_records_with_explicit_manifest(db, monkeypatch):
    issuer = _create_user_and_cabinet(db, clinic_id="issuer-clinic")
    _create_user_and_cabinet(
        db,
        clinic_id="legacy-active",
        plan=models.SubscriptionPlan.ELITE.value,
    )
    _create_user_and_cabinet(
        db,
        clinic_id="legacy-revoked",
        plan=models.SubscriptionPlan.PREMIUM.value,
    )
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", issuer.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)

    future = datetime.now(timezone.utc) + timedelta(days=60)
    expired = datetime.now(timezone.utc) - timedelta(days=2)
    docs = [
        ("legacy-active", {"active": True, "expiration_date": future}),
        ("legacy-revoked", {"active": True, "expiration_date": expired}),
    ]
    monkeypatch.setattr(migration, "_fetch_license_documents", lambda _service: docs)

    issued = []
    tokens = {}

    def fake_issue_license(**kwargs):
        issued.append(kwargs.copy())
        token = f"signed-{kwargs['cabinet_id']}"
        tokens[kwargs["cabinet_id"]] = token
        return token

    def fake_verify(token, cabinet_id, _now, *, allow_inactive=False):
        plan = next(item for item in issued if item["cabinet_id"] == cabinet_id)
        assert token == tokens[cabinet_id]
        assert allow_inactive is (plan["status"] != "ACTIVE")
        return _verified(plan, license_id=f"license-{cabinet_id}")

    async def fake_write(_self, public_id, signed_license):
        assert signed_license == tokens[public_id]
        return True

    def fake_read(_service, cabinet_id):
        return {"signed_license": tokens[cabinet_id]}

    monkeypatch.setattr(migration, "issue_license", fake_issue_license)
    monkeypatch.setattr(
        LicenseService,
        "_verify_signed_license",
        staticmethod(fake_verify),
    )
    monkeypatch.setattr(LicenseService, "write_signed_license", fake_write)
    monkeypatch.setattr(migration, "_read_license_document", fake_read)

    report = asyncio.run(
        migrate_legacy_licenses(
            db,
            issuer_user_id=issuer.id,
            apply=True,
            manifest={
                "legacy-active": {
                    "license_type": "PAID",
                    "feature_set": "GOLD",
                    "max_devices": 2,
                },
                "legacy-revoked": {
                    "license_type": "TRIAL",
                    "feature_set": "PREMIUM",
                    "max_devices": 1,
                },
            },
        )
    )

    assert report["ok"] is True
    assert report["applied"] is True
    assert len(report["migrated"]) == 2

    by_id = {item["cabinet_id"]: item for item in issued}
    active = by_id["legacy-active"]
    assert active["license_type"] == "PAID"
    assert active["status"] == "ACTIVE"
    assert active["feature_set"] == "GOLD"
    assert active["max_devices"] == 2

    revoked = by_id["legacy-revoked"]
    assert revoked["license_type"] == "TRIAL"
    assert revoked["status"] == "REVOKED"
    assert revoked["feature_set"] == "PREMIUM"
    assert revoked["max_devices"] == 1


def test_manifest_feature_set_is_required_and_never_inferred_from_sqlite(db, monkeypatch):
    issuer = _create_user_and_cabinet(db, clinic_id="issuer-clinic")
    _create_user_and_cabinet(
        db,
        clinic_id="legacy-local-elite",
        plan=models.SubscriptionPlan.ELITE.value,
    )
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", issuer.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(
        migration,
        "_fetch_license_documents",
        lambda _service: [
            (
                "legacy-local-elite",
                {
                    "active": True,
                    "expiration_date": datetime.now(timezone.utc) + timedelta(days=30),
                },
            )
        ],
    )

    report = asyncio.run(
        migrate_legacy_licenses(
            db,
            issuer_user_id=issuer.id,
            apply=False,
            manifest={
                "legacy-local-elite": {"license_type": "PAID", "max_devices": 1}
            },
        )
    )

    assert report["ok"] is False
    assert report["planned"] == []
    assert "requires feature_set" in report["manual"][0]["reason"]


def test_owner_type_is_forbidden_in_legacy_manifest(db, monkeypatch):
    issuer = _create_user_and_cabinet(db, clinic_id="issuer-clinic")
    _create_user_and_cabinet(db, clinic_id="legacy-owner-guess")
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", issuer.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(
        migration,
        "_fetch_license_documents",
        lambda _service: [
            (
                "legacy-owner-guess",
                {
                    "active": True,
                    "expiration_date": datetime.now(timezone.utc) + timedelta(days=30),
                },
            )
        ],
    )

    report = asyncio.run(
        migrate_legacy_licenses(
            db,
            issuer_user_id=issuer.id,
            apply=False,
            manifest={
                "legacy-owner-guess": {
                    "license_type": "OWNER",
                    "feature_set": "ELITE",
                    "max_devices": 1,
                }
            },
        )
    )

    assert report["ok"] is False
    assert report["manual"][0]["cabinet_id"] == "legacy-owner-guess"
    assert "OWNER is provisioned separately" in report["manual"][0]["reason"]
