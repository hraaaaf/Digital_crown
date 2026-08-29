"""Entry-flow truth: trial activation must not create new practitioner copies in CabinetConfig."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

from backend import models
from backend.security import get_password_hash


def _trial_code(db, *, email: str, code: str, cabinet_name: str = "Cabinet Trial"):
    row = models.TrialActivationCode(
        code=code,
        email=email,
        nom_complet="Dr Trial Canonical",
        cabinet_name=cabinet_name,
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=2),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _payload(email: str, code: str, cabinet_name: str = "Cabinet Trial"):
    return {
        "code": code,
        "email": email,
        "password": "TestPass123!",
        "nom_complet": "Dr Trial Canonical",
        "cabinet_name": cabinet_name,
        "accept_terms": True,
        "accept_privacy": True,
    }


def _mock_signed_control_plane(monkeypatch):
    """Keep identity tests on the signed SEC-1 path without requiring real key material."""
    expiry = datetime.now(timezone.utc) + timedelta(days=30)
    monkeypatch.setattr("backend.routers.public.settings.PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setattr(
        "backend.routers.public._sign_and_store_trial_license",
        AsyncMock(return_value="signed-test-license"),
    )
    monkeypatch.setattr(
        "backend.services.license_service.LicenseService._verify_signed_license",
        lambda *_, **__: SimpleNamespace(
            license_type="TRIAL",
            claims={"feature_set": models.SubscriptionPlan.GOLD.value},
            expires_at=expiry,
        ),
    )


def test_new_trial_stores_practitioner_on_user_not_cabinet(client, db, monkeypatch):
    email = "trial-entry-new@test.ma"
    code = "TRIAL-ENTRY-NEW"
    _trial_code(db, email=email, code=code)

    monkeypatch.setattr("backend.routers.public.invalidate_license_cache", lambda *_: None)
    _mock_signed_control_plane(monkeypatch)

    response = client.post("/api/public/activate-trial", json=_payload(email, code))
    assert response.status_code == 200, response.text

    user = db.query(models.User).filter(models.User.email == email).one()
    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).one()
    assert user.nom_complet == "Dr Trial Canonical"
    assert cabinet.nom_cabinet == "Cabinet Trial"
    assert cabinet.nom_praticien == ""
    assert cabinet.is_initialized is False


def test_existing_trial_does_not_overwrite_legacy_practitioner_copy(client, db, monkeypatch):
    email = "trial-entry-existing@test.ma"
    code = "TRIAL-ENTRY-OLD"
    _trial_code(db, email=email, code=code, cabinet_name="Cabinet Updated")

    user = models.User(
        email=email,
        hashed_password=get_password_hash("OldPass123!"),
        role=models.UserRole.DENTISTE,
        nom_complet="Old User Name",
        is_active=False,
        is_licensed=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    cabinet = models.CabinetConfig(
        owner_id=user.id,
        nom_cabinet="Cabinet Before",
        nom_praticien="LEGACY PRACTITIONER COPY",
        is_initialized=False,
    )
    db.add(cabinet)
    db.commit()

    monkeypatch.setattr("backend.routers.public.invalidate_license_cache", lambda *_: None)
    _mock_signed_control_plane(monkeypatch)

    response = client.post("/api/public/activate-trial", json=_payload(email, code, "Cabinet Updated"))
    assert response.status_code == 200, response.text

    db.refresh(user)
    db.refresh(cabinet)
    assert user.nom_complet == "Dr Trial Canonical"
    assert cabinet.nom_cabinet == "Cabinet Updated"
    assert cabinet.nom_praticien == "LEGACY PRACTITIONER COPY"
    assert cabinet.is_initialized is False
