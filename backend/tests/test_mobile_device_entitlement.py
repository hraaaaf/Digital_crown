"""SEC-1: signed max_devices is enforced at the mobile pairing boundary."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
import uuid

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from backend import models
from backend.license_security import VerifiedLicense
from backend.routers.mobile_pairing_secure import (
    _device_limit_from_entitlement,
    _serialize_pairing_write,
)
from backend.services.license_service import LicenseService


def _client_public_key_hex() -> str:
    private = ec.generate_private_key(ec.SECP256R1())
    return private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    ).hex()


def _prepare_pairing(db, user, *, token: str | None = None):
    config = models.CabinetConfig(
        owner_id=user.id,
        public_id=f"cab{user.id:013d}"[-16:],
        clinic_id=f"clinic-{user.id}",
        nom_cabinet="Cabinet Test",
        nom_praticien="Dr Test",
    )
    db.add(config)
    db.flush()
    record = models.ZKAPairingToken(
        token=token or str(uuid.uuid4()),
        employer_id=user.id,
        user_id=user.id,
        public_id=config.public_id,
        master_key="a" * 64,
        role="DENTISTE",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _add_device(db, user, *, revoked: bool = False):
    device = models.MobilePairedDevice(
        device_id=str(uuid.uuid4()),
        user_id=user.id,
        employer_id=user.id,
        client_public_key_hex="04" + "00" * 64,
        refresh_jti=f"refresh:{uuid.uuid4()}",
        revoked_at=datetime.utcnow() if revoked else None,
    )
    db.add(device)
    db.commit()
    return device


def _claim(client, token: str):
    return client.post(
        "/api/mobile/claim-token",
        json={"token": token, "client_public_key_hex": _client_public_key_hex()},
    )


def test_verified_result_preserves_signed_max_devices():
    verified = VerifiedLicense(
        claims={
            "license_id": "lic-1",
            "status": "ACTIVE",
            "license_type": "PAID",
            "feature_set": "GOLD",
            "release_channel": "stable",
            "max_devices": 3,
        },
        key_id="kid-1",
    )
    result = LicenseService._verified_result(verified, "test")
    assert result["max_devices"] == 3


def test_non_owner_entitlement_without_device_limit_fails_closed():
    with pytest.raises(Exception) as exc_info:
        _device_limit_from_entitlement(
            {"active": True, "license_type": "PAID", "max_devices": None}
        )
    exc = exc_info.value
    assert getattr(exc, "status_code", None) == 503


def test_pairing_denied_when_signed_device_limit_is_reached(client, db, dentiste):
    record = _prepare_pairing(db, dentiste)
    _add_device(db, dentiste)

    with patch(
        "backend.routers.mobile_pairing_secure.LicenseService.get_effective_license",
        new=AsyncMock(
            return_value={
                "active": True,
                "license_type": "PAID",
                "max_devices": 1,
                "release_channel": "stable",
            }
        ),
    ), patch("backend.utils.rate_limit.check_rate_limit", return_value=None):
        response = _claim(client, record.token)

    assert response.status_code == 409, response.text
    detail = response.json()["detail"]
    assert detail["code"] == "MOBILE_DEVICE_LIMIT_REACHED"
    assert detail["max_devices"] == 1
    assert detail["active_devices"] == 1
    db.refresh(record)
    assert record.used_at is None
    assert (
        db.query(models.MobilePairedDevice)
        .filter(models.MobilePairedDevice.employer_id == dentiste.id)
        .count()
        == 1
    )


def test_revoked_device_releases_capacity_for_new_pairing(client, db, dentiste):
    record = _prepare_pairing(db, dentiste)
    _add_device(db, dentiste, revoked=True)

    with patch(
        "backend.routers.mobile_pairing_secure.LicenseService.get_effective_license",
        new=AsyncMock(
            return_value={
                "active": True,
                "license_type": "PAID",
                "max_devices": 1,
                "release_channel": "stable",
            }
        ),
    ), patch("backend.utils.rate_limit.check_rate_limit", return_value=None):
        response = _claim(client, record.token)

    assert response.status_code == 200, response.text
    assert response.json()["device_entitlement"]["max_devices"] == 1
    assert response.json()["device_entitlement"]["active_devices"] == 1
    db.refresh(record)
    assert record.used_at is not None
    assert (
        db.query(models.MobilePairedDevice)
        .filter(
            models.MobilePairedDevice.employer_id == dentiste.id,
            models.MobilePairedDevice.revoked_at.is_(None),
        )
        .count()
        == 1
    )


def test_missing_signed_device_entitlement_does_not_consume_pairing_token(
    client, db, dentiste
):
    record = _prepare_pairing(db, dentiste)

    with patch(
        "backend.routers.mobile_pairing_secure.LicenseService.get_effective_license",
        new=AsyncMock(
            return_value={
                "active": True,
                "license_type": "TRIAL",
                "max_devices": None,
            }
        ),
    ), patch("backend.utils.rate_limit.check_rate_limit", return_value=None):
        response = _claim(client, record.token)

    assert response.status_code == 503, response.text
    db.refresh(record)
    assert record.used_at is None
    assert db.query(models.MobilePairedDevice).count() == 0


def test_sqlite_pairing_reservation_is_exclusive_across_sessions(tmp_path):
    db_path = tmp_path / "pairing-lock.sqlite"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"timeout": 0.05, "check_same_thread": False},
    )
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    first = Session()
    second = Session()
    try:
        _serialize_pairing_write(first, employer_id=1)
        with pytest.raises(OperationalError):
            _serialize_pairing_write(second, employer_id=1)

        first.rollback()
        _serialize_pairing_write(second, employer_id=1)
        second.rollback()
    finally:
        first.close()
        second.close()
        engine.dispose()
