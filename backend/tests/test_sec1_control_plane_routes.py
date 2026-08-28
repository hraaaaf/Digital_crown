import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from backend import models
from backend.config import settings
from backend.routers import license_control_plane as control_plane
from backend.security import get_password_hash


class _Snapshot:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return dict(self._data or {})


class _DocRef:
    def __init__(self, store, key):
        self.store = store
        self.key = key

    def get(self):
        return _Snapshot(self.store.get(self.key))

    def set(self, data, **_kwargs):
        self.store[self.key] = dict(data)


class _Collection:
    def __init__(self, store):
        self.store = store

    def document(self, key):
        return _DocRef(self.store, key)


class _Firestore:
    def __init__(self):
        self.collections = {}

    def collection(self, name):
        return _Collection(self.collections.setdefault(name, {}))


class _LicenseService:
    def __init__(self):
        self._db = _Firestore()
        self.writes = []

    async def write_signed_license(self, public_id, signed_license):
        self.writes.append((public_id, signed_license))
        return True


def _trial(db, *, code="DC-TEST-0001", email="prospect@example.com"):
    admin = models.User(
        email="issuer@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        role=models.UserRole.ADMIN,
        nom_complet="Issuer",
        is_active=True,
    )
    db.add(admin)
    db.flush()
    trial = models.TrialActivationCode(
        code=code,
        email=email,
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=10),
        created_by_admin_id=admin.id,
    )
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial


def test_control_plane_route_is_absent_when_disabled(db, monkeypatch):
    _trial(db)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            control_plane.activate_trial(
                control_plane.TrialControlPlaneActivation(
                    code="DC-TEST-0001",
                    email="prospect@example.com",
                    cabinet_id="cab-001",
                ),
                request=None,
                db=db,
            )
        )
    assert exc.value.status_code == 404


def test_same_trial_redemption_is_idempotent_and_different_cabinet_is_rejected(db, monkeypatch):
    trial = _trial(db)
    service = _LicenseService()
    issued = []

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(control_plane, "LicenseService", lambda: service)

    def fake_issue_license(**kwargs):
        issued.append(dict(kwargs))
        return "signed-trial-token"

    monkeypatch.setattr(control_plane, "issue_license", fake_issue_license)

    payload = control_plane.TrialControlPlaneActivation(
        code=trial.code,
        email=trial.email,
        cabinet_id="cab-stable-001",
    )
    first = asyncio.run(control_plane.activate_trial(payload, request=None, db=db))
    second = asyncio.run(control_plane.activate_trial(payload, request=None, db=db))

    assert first == second
    assert first["signed_license"] == "signed-trial-token"
    assert first["license_type"] == "TRIAL"
    assert first["feature_set"] == models.SubscriptionPlan.GOLD.value
    assert len(issued) == 1
    assert len(service.writes) == 1
    db.refresh(trial)
    assert trial.consumed_at is not None

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            control_plane.activate_trial(
                control_plane.TrialControlPlaneActivation(
                    code=trial.code,
                    email=trial.email,
                    cabinet_id="cab-attacker-002",
                ),
                request=None,
                db=db,
            )
        )
    assert exc.value.status_code == 400
    assert len(issued) == 1


def test_trial_code_is_bound_to_email_before_signing(db, monkeypatch):
    _trial(db)
    service = _LicenseService()
    calls = []

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(control_plane, "LicenseService", lambda: service)
    monkeypatch.setattr(control_plane, "issue_license", lambda **kwargs: calls.append(kwargs) or "token")

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            control_plane.activate_trial(
                control_plane.TrialControlPlaneActivation(
                    code="DC-TEST-0001",
                    email="attacker@example.com",
                    cabinet_id="cab-001",
                ),
                request=None,
                db=db,
            )
        )

    assert exc.value.status_code == 400
    assert calls == []
    assert service.writes == []
