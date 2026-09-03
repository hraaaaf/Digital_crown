import base64
from datetime import datetime, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat

from backend.config import settings
from backend.license_trust import TRUSTED_LICENSE_PUBLIC_KEYS
from backend.services.license_service import LicenseService


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _enable_signed_control_plane(monkeypatch):
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    monkeypatch.setattr(settings, "PLATFORM_CONTROL_PLANE_ENABLED", True)
    monkeypatch.setenv("DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL", _b64url(private_raw))
    monkeypatch.setenv("DIGITALCROWN_LICENSE_SIGNING_KEY_ID", "test-public-k1")
    monkeypatch.setitem(TRUSTED_LICENSE_PUBLIC_KEYS, "test-public-k1", _b64url(public_raw))

    async def _persist_signed_license(_self, public_id: str, signed_license: str) -> bool:
        assert public_id
        assert signed_license.count(".") == 2
        return True

    monkeypatch.setattr(LicenseService, "write_signed_license", _persist_signed_license)


def test_preview_trial_code_success(client, db, monkeypatch):
    from backend import models

    _enable_signed_control_plane(monkeypatch)
    code = models.TrialActivationCode(
        code="DC-PREVIEW-01",
        email="preview@cabinet.ma",
        nom_complet="Dr Preview",
        cabinet_name="Cabinet Preview",
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(code)
    db.commit()

    r = client.get("/api/public/trial-code/DC-PREVIEW-01")
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "preview@cabinet.ma"
    assert body["trial_days"] == 30


def test_activate_trial_code_creates_active_user_and_uninitialized_cabinet(client, db, monkeypatch):
    from backend import models

    _enable_signed_control_plane(monkeypatch)
    issuer = models.User(
        email="issuer-public-activation@digitalcrown.local",
        hashed_password="unused",
        role=models.UserRole.ADMIN,
        nom_complet="Issuer",
        is_active=True,
    )
    db.add(issuer)
    db.flush()

    code = models.TrialActivationCode(
        code="DC-ACT-0001",
        email="activate@cabinet.ma",
        nom_complet="Dr Activate",
        cabinet_name="Cabinet Activate",
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=7),
        created_by_admin_id=issuer.id,
    )
    db.add(code)
    db.commit()

    r = client.post(
        "/api/public/activate-trial",
        json={
            "code": "DC-ACT-0001",
            "email": "activate@cabinet.ma",
            "password": "Pass1234",
            "nom_complet": "Dr Activate",
            "cabinet_name": "Cabinet Activate",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert r.status_code == 200, r.text

    user = db.query(models.User).filter(models.User.email == "activate@cabinet.ma").first()
    assert user is not None
    assert user.is_active is True
    assert user.is_licensed is True
    assert user.subscription_plan == "GOLD"

    cabinet = db.query(models.CabinetConfig).filter(models.CabinetConfig.owner_id == user.id).first()
    assert cabinet is not None
    assert cabinet.is_initialized is False

    db.refresh(code)
    assert code.consumed_at is not None


def test_activate_trial_code_rejects_email_mismatch(client, db, monkeypatch):
    from backend import models

    _enable_signed_control_plane(monkeypatch)
    code = models.TrialActivationCode(
        code="DC-MISMATCH-01",
        email="expected@cabinet.ma",
        trial_days=30,
        expires_at=datetime.utcnow() + timedelta(days=7),
    )
    db.add(code)
    db.commit()

    r = client.post(
        "/api/public/activate-trial",
        json={
            "code": "DC-MISMATCH-01",
            "email": "other@cabinet.ma",
            "password": "Pass1234",
            "nom_complet": "Dr Other",
            "accept_terms": True,
            "accept_privacy": True,
        },
    )
    assert r.status_code == 400
