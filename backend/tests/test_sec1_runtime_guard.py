import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend import models
from backend.config import settings
from backend.routers import auth
from backend.services.license_service import LicenseService


class _Query:
    def __init__(self, value):
        self.value = value

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.value


class _DB:
    def __init__(self, cabinet):
        self.cabinet = cabinet

    def query(self, model):
        if model is models.CabinetConfig:
            return _Query(self.cabinet)
        return _Query(None)


def _request(method: str, path: str) -> Request:
    return Request({
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
        "scheme": "https",
        "server": ("test", 443),
        "client": ("127.0.0.1", 12345),
    })


def _owner(**overrides):
    data = {
        "id": 7,
        "employer_id": None,
        "is_licensed": True,  # deliberately mutable/local and therefore non-authoritative
        "subscription_plan": models.SubscriptionPlan.ELITE.value,
        "is_suspended": False,
        "is_archived": False,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_mutation_rejects_forged_sqlite_license_flag(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "cabinet")
    user = _owner(is_licensed=True)
    cabinet = SimpleNamespace(clinic_id="cab-sec1", public_id="public-sec1")

    async def fake_effective_license(_self, clinic_id):
        assert clinic_id == "cab-sec1"
        return {"active": False, "reason": "invalid_signature_or_claims"}

    monkeypatch.setattr(LicenseService, "get_effective_license", fake_effective_license)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            auth._enforce_signed_license_for_mutation(
                _request("POST", "/api/patients"),
                _DB(cabinet),
                user,
            )
        )

    assert exc.value.status_code == 403
    assert exc.value.detail == "invalid_signature_or_claims"


def test_mutation_accepts_valid_signed_license_even_if_sqlite_flag_is_false(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "cabinet")
    user = _owner(is_licensed=False)
    cabinet = SimpleNamespace(clinic_id="cab-sec1", public_id="public-sec1")

    async def fake_effective_license(_self, _clinic_id):
        return {
            "active": True,
            "license_type": "PAID",
            "feature_set": models.SubscriptionPlan.GOLD.value,
        }

    monkeypatch.setattr(LicenseService, "get_effective_license", fake_effective_license)

    asyncio.run(
        auth._enforce_signed_license_for_mutation(
            _request("PATCH", "/api/patients/12"),
            _DB(cabinet),
            user,
        )
    )


def test_elite_access_ignores_forged_local_plan(monkeypatch):
    user = _owner(subscription_plan=models.SubscriptionPlan.ELITE.value)

    async def fake_state(_db, _user):
        return {
            "active": True,
            "license_type": "PAID",
            "feature_set": models.SubscriptionPlan.GOLD.value,
        }

    monkeypatch.setattr(auth, "_get_signed_license_state", fake_state)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_elite_license(current_user=user, db=object()))

    assert exc.value.status_code == 403
    assert "ELITE" in exc.value.detail


def test_owner_signed_entitlement_bypasses_commercial_feature_set(monkeypatch):
    user = _owner(subscription_plan=models.SubscriptionPlan.GOLD.value)

    async def fake_state(_db, _user):
        return {
            "active": True,
            "license_type": "OWNER",
            "feature_set": "owner",
        }

    monkeypatch.setattr(auth, "_get_signed_license_state", fake_state)

    result = asyncio.run(auth.require_elite_license(current_user=user, db=object()))
    assert result is user
