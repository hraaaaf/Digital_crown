import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend import models
from backend.config import settings
from backend.routers import license_control_plane as control_plane
from backend.security import get_password_hash


DEVICE_ID = "a" * 64
DEVICE_PUBLIC_KEY = "device-public-key-test"


class _Snapshot:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return dict(self._data or {})


class _DocRef:
    def __init__(self, db, collection_name, key):
        self.db = db
        self.collection_name = collection_name
        self.key = key

    @property
    def store(self):
        return self.db.collections.setdefault(self.collection_name, {})

    def get(self):
        return _Snapshot(self.store.get(self.key))

    def set(self, data, **_kwargs):
        self.store[self.key] = dict(data)


class _Collection:
    def __init__(self, db, name):
        self.db = db
        self.name = name

    def document(self, key):
        return _DocRef(self.db, self.name, key)


class _Batch:
    def __init__(self, db):
        self.db = db
        self.operations = []

    def set(self, ref, data, merge=False):
        self.operations.append(("set", ref, dict(data), bool(merge)))

    def create(self, ref, data):
        self.operations.append(("create", ref, dict(data), False))

    def commit(self):
        if self.db.fail_before_apply:
            self.db.fail_before_apply = False
            raise RuntimeError("forced atomic commit failure")

        for op, ref, _data, _merge in self.operations:
            if op == "create" and ref.key in ref.store:
                raise RuntimeError("document already exists")

        for op, ref, data, merge in self.operations:
            if op == "set" and merge and ref.key in ref.store:
                ref.store[ref.key] = {**ref.store[ref.key], **data}
            else:
                ref.store[ref.key] = dict(data)

        self.db.batch_commits += 1
        if self.db.raise_after_apply:
            self.db.raise_after_apply = False
            raise RuntimeError("simulated lost commit acknowledgement")
        return []


class _Firestore:
    def __init__(self):
        self.collections = {}
        self.batch_commits = 0
        self.fail_before_apply = False
        self.raise_after_apply = False

    def collection(self, name):
        return _Collection(self, name)

    def batch(self):
        return _Batch(self)


class _LicenseService:
    def __init__(self):
        self._db = _Firestore()

    def _verify_signed_license(self, signed_license, cabinet_id, now, *, allow_inactive=False):
        assert signed_license
        assert cabinet_id
        assert allow_inactive is True
        return SimpleNamespace(
            status="ACTIVE",
            license_type="TRIAL",
            expires_at=now + timedelta(days=30),
            claims={
                "feature_set": models.SubscriptionPlan.GOLD.value,
                "release_channel": "stable",
            },
            license_id="lic-test-001",
            key_id="k1",
        )


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


def _activation_payload(trial, *, cabinet_id="cab-stable-001", device_id=DEVICE_ID):
    return control_plane.TrialControlPlaneActivation(
        code=trial.code,
        email=trial.email,
        cabinet_id=cabinet_id,
        device_id=device_id,
        device_public_key=DEVICE_PUBLIC_KEY,
        platform="windows",
    )


def _activate(db, trial, *, cabinet_id="cab-stable-001", device_id=DEVICE_ID):
    return asyncio.run(
        control_plane.activate_trial(
            _activation_payload(trial, cabinet_id=cabinet_id, device_id=device_id),
            request=None,
            db=db,
        )
    )


def _patch_issuers(monkeypatch, issued):
    def fake_issue_license(**kwargs):
        issued.append(("license", dict(kwargs)))
        return "signed-trial-token"

    def fake_issue_device_certificate(**kwargs):
        issued.append(("device", dict(kwargs)))
        return "signed-device-certificate"

    monkeypatch.setattr(control_plane, "issue_license", fake_issue_license)
    monkeypatch.setattr(control_plane, "issue_device_certificate", fake_issue_device_certificate)


def test_control_plane_route_is_absent_when_disabled(db, monkeypatch):
    trial = _trial(db)
    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", False)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            control_plane.activate_trial(
                _activation_payload(trial),
                request=None,
                db=db,
            )
        )
    assert exc.value.status_code == 404


def test_same_trial_redemption_is_idempotent_and_other_device_or_cabinet_is_rejected(db, monkeypatch):
    trial = _trial(db)
    service = _LicenseService()
    issued = []

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(control_plane, "LicenseService", lambda: service)
    _patch_issuers(monkeypatch, issued)

    first = _activate(db, trial)
    second = _activate(db, trial)

    assert first == second
    assert first["signed_license"] == "signed-trial-token"
    assert first["signed_device_certificate"] == "signed-device-certificate"
    assert first["device_id"] == DEVICE_ID
    assert first["license_type"] == "TRIAL"
    assert first["feature_set"] == models.SubscriptionPlan.GOLD.value
    assert [kind for kind, _ in issued] == ["license", "device"]
    assert service._db.batch_commits == 1
    assert service._db.collections["licenses"]["cab-stable-001"]["signed_license"] == "signed-trial-token"
    assert len(service._db.collections["trial_redemptions"]) == 1
    assert len(service._db.collections["license_devices"]) == 1
    device_doc = next(iter(service._db.collections["license_devices"].values()))
    assert device_doc["device_id"] == DEVICE_ID
    assert device_doc["license_id"] == "lic-test-001"
    db.refresh(trial)
    assert trial.consumed_at is not None

    with pytest.raises(HTTPException) as exc:
        _activate(db, trial, cabinet_id="cab-attacker-002")
    assert exc.value.status_code == 400

    with pytest.raises(HTTPException) as exc:
        _activate(db, trial, device_id="b" * 64)
    assert exc.value.status_code == 400
    assert len(issued) == 2
    assert service._db.batch_commits == 1


def test_trial_code_is_bound_to_email_before_signing(db, monkeypatch):
    trial = _trial(db)
    service = _LicenseService()
    issued = []

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(control_plane, "LicenseService", lambda: service)
    _patch_issuers(monkeypatch, issued)

    bad = _activation_payload(trial)
    bad.email = "attacker@example.com"
    with pytest.raises(HTTPException) as exc:
        asyncio.run(control_plane.activate_trial(bad, request=None, db=db))

    assert exc.value.status_code == 400
    assert issued == []
    assert service._db.batch_commits == 0


def test_atomic_commit_failure_leaves_no_license_device_or_redemption(db, monkeypatch):
    trial = _trial(db)
    service = _LicenseService()
    service._db.fail_before_apply = True
    issued = []

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(control_plane, "LicenseService", lambda: service)
    _patch_issuers(monkeypatch, issued)

    with pytest.raises(HTTPException) as exc:
        _activate(db, trial)

    assert exc.value.status_code == 503
    assert service._db.collections.get("licenses", {}) == {}
    assert service._db.collections.get("license_devices", {}) == {}
    assert service._db.collections.get("trial_redemptions", {}) == {}
    db.refresh(trial)
    assert trial.consumed_at is None


def test_lost_commit_ack_recovers_same_device_redemption_without_reissuing(db, monkeypatch):
    trial = _trial(db)
    service = _LicenseService()
    service._db.raise_after_apply = True
    issued = []

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(control_plane, "check_rate_limit", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(control_plane, "LicenseService", lambda: service)
    _patch_issuers(monkeypatch, issued)

    first = _activate(db, trial)
    second = _activate(db, trial)

    assert first == second
    assert len(issued) == 2
    assert service._db.batch_commits == 1
    assert len(service._db.collections["trial_redemptions"]) == 1
    assert len(service._db.collections["license_devices"]) == 1
    assert service._db.collections["licenses"]["cab-stable-001"]["signed_license"] == "signed-trial-token"
    db.refresh(trial)
    assert trial.consumed_at is not None
