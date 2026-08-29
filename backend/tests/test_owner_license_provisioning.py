import asyncio

import pytest

from backend import models
from backend.config import settings
from backend.license_security import VerifiedLicense
from backend.owner_license_provisioning import (
    OwnerProvisioningError,
    provision_owner_license,
)
from backend import owner_license_provisioning as owner_provisioning
from backend.services.license_service import LicenseService


def _create_owner(db, *, email="owner-sec1@example.com"):
    owner = models.User(
        email=email,
        hashed_password="unused",
        role=models.UserRole.ADMIN,
        nom_complet="Owner SEC1",
        is_active=True,
        is_licensed=False,
        subscription_plan=models.SubscriptionPlan.GOLD.value,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


def _create_cabinet(db, owner_id: int, clinic_id="owner-sec1-clinic"):
    cabinet = models.CabinetConfig(
        owner_id=owner_id,
        clinic_id=clinic_id,
        nom_cabinet="Owner SEC1",
        nom_praticien="Owner SEC1",
    )
    db.add(cabinet)
    db.commit()
    db.refresh(cabinet)
    return cabinet


def _verified_owner(owner_id: int, clinic_id: str, license_id="owner-license-1"):
    return VerifiedLicense(
        claims={
            "license_id": license_id,
            "cabinet_id": clinic_id,
            "license_type": "OWNER",
            "status": "ACTIVE",
            "subject_user_id": owner_id,
            "expires_at": None,
            "feature_set": models.SubscriptionPlan.ELITE.value,
            "max_devices": None,
        },
        key_id="test-owner-k1",
    )


def _patch_issuer_and_verifier(monkeypatch, owner_id: int, clinic_id: str):
    issued = {}

    def fake_issue_license(**kwargs):
        issued.update(kwargs)
        return "signed.owner.token"

    def fake_verify(token, expected_clinic_id, _now, *, allow_inactive=False):
        assert token == "signed.owner.token"
        assert expected_clinic_id == clinic_id
        assert allow_inactive is False
        return _verified_owner(owner_id, clinic_id)

    monkeypatch.setattr(owner_provisioning, "issue_license", fake_issue_license)
    monkeypatch.setattr(
        LicenseService,
        "_verify_signed_license",
        staticmethod(fake_verify),
    )
    return issued


def test_owner_provisioning_fails_closed_outside_control_plane(db, monkeypatch):
    owner = _create_owner(db)
    _create_cabinet(db, owner.id)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)

    with pytest.raises(OwnerProvisioningError, match="control-plane-only"):
        asyncio.run(
            provision_owner_license(db, owner_user_id=owner.id, apply=False)
        )


def test_owner_provisioning_requires_exact_immutable_owner_id(db, monkeypatch):
    owner = _create_owner(db)
    _create_cabinet(db, owner.id)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)

    with pytest.raises(OwnerProvisioningError, match="does not match"):
        asyncio.run(
            provision_owner_license(db, owner_user_id=owner.id + 1, apply=False)
        )


def test_owner_dry_run_signs_exact_owner_claims_without_persisting(db, monkeypatch):
    owner = _create_owner(db)
    cabinet = _create_cabinet(db, owner.id)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    issued = _patch_issuer_and_verifier(monkeypatch, owner.id, cabinet.clinic_id)

    async def must_not_write(*_args, **_kwargs):
        raise AssertionError("dry-run must not persist")

    monkeypatch.setattr(LicenseService, "write_signed_license", must_not_write)

    result = asyncio.run(
        provision_owner_license(db, owner_user_id=owner.id, apply=False)
    )

    assert result["ok"] is True
    assert result["applied"] is False
    assert result["source"] == "dry-run"
    assert "signed_license" not in result
    assert issued == {
        "cabinet_id": cabinet.clinic_id,
        "license_type": "OWNER",
        "created_by_user_id": owner.id,
        "expires_at": None,
        "release_channel": "stable",
        "feature_set": models.SubscriptionPlan.ELITE.value,
        "max_devices": None,
        "status": "ACTIVE",
        "subject_user_id": owner.id,
    }
    db.refresh(owner)
    assert owner.is_licensed is False
    assert owner.subscription_plan == models.SubscriptionPlan.GOLD.value


def test_owner_apply_requires_matching_firebase_readback_before_sqlite_mirror(db, monkeypatch):
    owner = _create_owner(db)
    cabinet = _create_cabinet(db, owner.id)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    _patch_issuer_and_verifier(monkeypatch, owner.id, cabinet.clinic_id)

    async def fake_write(_self, public_id, signed_license):
        assert public_id == cabinet.clinic_id
        assert signed_license == "signed.owner.token"
        return True

    calls = {"read": 0}

    async def fake_validate(_self, clinic_id):
        calls["read"] += 1
        assert clinic_id == cabinet.clinic_id
        if calls["read"] == 1:
            return {
                "active": False,
                "source": "firebase",
                "license_type": "PAID",
                "feature_set": models.SubscriptionPlan.GOLD.value,
                "expiration_date": None,
            }
        return {
            "active": True,
            "source": "firebase",
            "license_type": "OWNER",
            "feature_set": models.SubscriptionPlan.ELITE.value,
            "expiration_date": None,
            "license_id": "owner-license-1",
        }

    monkeypatch.setattr(LicenseService, "write_signed_license", fake_write)
    monkeypatch.setattr(LicenseService, "validate_license_with_expiry", fake_validate)

    result = asyncio.run(
        provision_owner_license(db, owner_user_id=owner.id, apply=True)
    )

    assert result["applied"] is True
    assert result["source"] == "firebase"
    db.refresh(owner)
    assert owner.is_licensed is True
    assert owner.subscription_plan == models.SubscriptionPlan.ELITE.value
    assert owner.license_expires_at is None
    history = (
        db.query(models.LicenseHistory)
        .filter(models.LicenseHistory.user_id == owner.id)
        .order_by(models.LicenseHistory.id.desc())
        .first()
    )
    assert history is not None
    assert history.action == "OWNER_ENTITLEMENT_ISSUED_SIGNED"


def test_owner_apply_refuses_mismatched_firebase_readback_without_sqlite_mutation(db, monkeypatch):
    owner = _create_owner(db)
    cabinet = _create_cabinet(db, owner.id)
    monkeypatch.setattr(settings, "SUPERADMIN_USER_ID", owner.id)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    _patch_issuer_and_verifier(monkeypatch, owner.id, cabinet.clinic_id)

    async def fake_write(_self, public_id, signed_license):
        assert public_id == cabinet.clinic_id
        assert signed_license == "signed.owner.token"
        return True

    calls = {"read": 0}

    async def fake_validate(_self, _clinic_id):
        calls["read"] += 1
        return {
            "active": calls["read"] > 1,
            "source": "firebase",
            "license_type": "PAID",
            "feature_set": models.SubscriptionPlan.GOLD.value,
            "expiration_date": None,
            "license_id": "different-license",
        }

    monkeypatch.setattr(LicenseService, "write_signed_license", fake_write)
    monkeypatch.setattr(LicenseService, "validate_license_with_expiry", fake_validate)

    with pytest.raises(OwnerProvisioningError, match="read-back"):
        asyncio.run(
            provision_owner_license(db, owner_user_id=owner.id, apply=True)
        )

    db.refresh(owner)
    assert owner.is_licensed is False
    assert owner.subscription_plan == models.SubscriptionPlan.GOLD.value
