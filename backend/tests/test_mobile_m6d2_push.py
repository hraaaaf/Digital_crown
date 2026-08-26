from datetime import datetime
from pathlib import Path
import json
from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from backend import models
from backend.models_mobile_push import MobilePushSubscription
from backend.routers import mobile as mobile_router
from backend.routers import mobile_push
from backend.services import mobile_push_service
from backend.services.mobile_notification_policy import (
    FINANCIAL_NOTIFICATION_PREFIXES,
    user_can_receive_mobile_notification,
)


def _user(*, permissions):
    return SimpleNamespace(
        role="DENTISTE",
        employer_id=42,
        permissions=permissions,
        email="employee@example.test",
    )


def _db_user(db, email: str, *, employer_id: int | None = None):
    user = models.User(
        email=email,
        hashed_password="test-only-hash",
        role=models.UserRole.DENTISTE,
        nom_complet=email,
        is_active=True,
        is_licensed=True,
        is_suspended=False,
        is_archived=False,
        employer_id=employer_id,
        approval_status="approved",
        permissions={"patients": True, "accounting": False, "payments": False},
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _paired_device(db, *, device_id: str, user_id: int, employer_id: int, revoked_at=None):
    device = models.MobilePairedDevice(
        device_id=device_id,
        user_id=user_id,
        employer_id=employer_id,
        client_public_key_hex="04" + "11" * 64,
        refresh_jti=f"refresh-{device_id}",
        revoked_at=revoked_at,
    )
    db.add(device)
    db.commit()
    return device


def _subscription_body(endpoint: str) -> mobile_push.PushSubscriptionRequest:
    return mobile_push.PushSubscriptionRequest(
        endpoint=endpoint,
        keys={"p256dh": "A" * 43, "auth": "B" * 22},
        platform="web",
    )


def test_push_policy_matches_in_app_financial_boundary():
    assert FINANCIAL_NOTIFICATION_PREFIXES == mobile_router._FINANCIAL_NOTIFICATION_PREFIXES

    patient_only = _user(permissions={"patients": True, "accounting": False, "payments": False})
    assert user_can_receive_mobile_notification(patient_only, "STOCK_GANTS") is True
    assert user_can_receive_mobile_notification(patient_only, "OVERDUE_PAYMENT") is False
    assert user_can_receive_mobile_notification(patient_only, "HIGH_VALUE_RISK_15000") is False
    assert user_can_receive_mobile_notification(patient_only, "ORTHO_SEMESTER_2") is False

    finance_user = _user(permissions={"patients": True, "accounting": True, "payments": False})
    assert user_can_receive_mobile_notification(finance_user, "OVERDUE_PAYMENT") is True

    finance_without_patients = _user(permissions={"patients": False, "accounting": True, "payments": True})
    assert user_can_receive_mobile_notification(finance_without_patients, "OVERDUE_PAYMENT") is False


def test_os_payload_is_generic_and_patient_free():
    payload = mobile_push_service.GENERIC_OS_PUSH_PAYLOAD
    assert payload == {"kind": "alerts"}
    serialized = json.dumps(payload).lower()
    assert "patient" not in serialized
    assert "paiement" not in serialized
    assert "montant" not in serialized


def test_vapid_keypair_is_persistent_and_not_silently_rotated(tmp_path, monkeypatch):
    target = tmp_path / "web_push_vapid.json"
    monkeypatch.setattr(mobile_push_service, "_vapid_key_path", lambda: target)

    private_1, public_1 = mobile_push_service.get_or_create_vapid_keypair()
    private_2, public_2 = mobile_push_service.get_or_create_vapid_keypair()

    assert target.exists()
    assert private_1 == private_2
    assert public_1 == public_2
    assert public_1
    assert private_1
    assert "PRIVATE KEY" not in private_1

    target.write_text('{"version":1,"private_key_b64":"broken","public_key":"broken"}', encoding="utf-8")
    with pytest.raises(RuntimeError, match="VAPID"):
        mobile_push_service.get_or_create_vapid_keypair()


def test_push_endpoint_rejects_private_network_ssrf(monkeypatch):
    monkeypatch.setattr(
        mobile_push_service.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("192.168.1.50", 443))],
    )
    assert mobile_push_service._is_public_push_endpoint("https://push.example.test/sub") is False

    monkeypatch.setattr(
        mobile_push_service.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("8.8.8.8", 443))],
    )
    assert mobile_push_service._is_public_push_endpoint("https://push.example.test/sub") is True
    assert mobile_push_service._is_public_push_endpoint("http://push.example.test/sub") is False


def test_lan_url_override_tracks_secure_launcher(monkeypatch):
    monkeypatch.setattr(mobile_push._legacy, "_detect_lan_ip", lambda: "192.168.10.20")
    monkeypatch.setenv("DIGITALCROWN_ENABLE_HTTPS", "true")
    mobile_push.install_secure_lan_url_overrides()
    assert mobile_push._legacy.get_lan_base_url() == "https://192.168.10.20:8005"
    assert mobile_push._legacy.get_lan_frontend_url() == "https://192.168.10.20:5173"

    monkeypatch.setenv("DIGITALCROWN_ENABLE_HTTPS", "false")
    assert mobile_push._legacy.get_lan_base_url() == "http://192.168.10.20:8005"


def test_subscription_model_and_service_are_device_revocation_bound():
    model_source = Path("backend/models_mobile_push.py").read_text(encoding="utf-8")
    service_source = Path("backend/services/mobile_push_service.py").read_text(encoding="utf-8")
    router_source = Path("backend/routers/mobile_push.py").read_text(encoding="utf-8")

    assert 'ForeignKey("mobile_paired_devices.device_id"' in model_source
    assert 'UniqueConstraint("device_id"' in model_source
    assert "vapid_public_key" in model_source
    assert "MobilePairedDevice.revoked_at.is_(None)" in service_source
    assert "MobilePairedDevice.user_id == MobilePushSubscription.user_id" in service_source
    assert "MobilePairedDevice.employer_id == MobilePushSubscription.employer_id" in service_source
    assert "_decode_mobile_identity(authorization, db)" in router_source
    assert "payload_contains_patient_data\": False" in router_source


def test_scheduler_passes_types_not_patient_content_to_push():
    source = Path("backend/services/daily_scheduler.py").read_text(encoding="utf-8")
    assert "new_types_by_employer" in source
    assert "send_push_for_alert_types(db, emp_id, alert_types)" in source
    assert "title=f\"Digital Crown" not in source
    assert "body=\"Consultez votre tableau" not in source


def test_subscription_endpoint_cannot_cross_active_devices_but_transfers_after_revocation(db, monkeypatch):
    owner = _db_user(db, "push-owner@example.test")
    employee = _db_user(db, "push-employee@example.test", employer_id=owner.id)
    device_a = _paired_device(
        db,
        device_id="11111111-1111-4111-8111-111111111111",
        user_id=owner.id,
        employer_id=owner.id,
    )
    device_b = _paired_device(
        db,
        device_id="22222222-2222-4222-8222-222222222222",
        user_id=employee.id,
        employer_id=owner.id,
    )
    monkeypatch.setattr(mobile_push, "get_or_create_vapid_keypair", lambda: ("private", "public-key"))

    endpoint = "https://push.example.test/subscription/shared"
    body = _subscription_body(endpoint)
    identity_a = mobile_push.MobilePushIdentity(user=owner, tenant_id=owner.id, device_id=device_a.device_id)
    identity_b = mobile_push.MobilePushIdentity(user=employee, tenant_id=owner.id, device_id=device_b.device_id)

    result = mobile_push.register_mobile_push_subscription(body, identity=identity_a, db=db)
    assert result["status"] == "registered"

    with pytest.raises(HTTPException) as conflict:
        mobile_push.register_mobile_push_subscription(body, identity=identity_b, db=db)
    assert conflict.value.status_code == 409

    device_a.revoked_at = datetime.utcnow()
    db.commit()

    result = mobile_push.register_mobile_push_subscription(body, identity=identity_b, db=db)
    assert result["status"] == "registered"
    rows = db.query(MobilePushSubscription).filter(MobilePushSubscription.endpoint == endpoint).all()
    assert len(rows) == 1
    assert rows[0].device_id == device_b.device_id
    assert rows[0].user_id == employee.id
    assert rows[0].employer_id == owner.id


def test_push_delivery_excludes_revoked_device_and_targets_active_authorized_user(db, monkeypatch):
    owner = _db_user(db, "delivery-owner@example.test")
    employee = _db_user(db, "delivery-employee@example.test", employer_id=owner.id)
    revoked_device = _paired_device(
        db,
        device_id="33333333-3333-4333-8333-333333333333",
        user_id=owner.id,
        employer_id=owner.id,
        revoked_at=datetime.utcnow(),
    )
    active_device = _paired_device(
        db,
        device_id="44444444-4444-4444-8444-444444444444",
        user_id=employee.id,
        employer_id=owner.id,
    )
    db.add_all([
        MobilePushSubscription(
            device_id=revoked_device.device_id,
            user_id=owner.id,
            employer_id=owner.id,
            endpoint="https://push.example.test/subscription/revoked",
            p256dh="A" * 43,
            auth="B" * 22,
            platform="web",
            vapid_public_key="public-key",
        ),
        MobilePushSubscription(
            device_id=active_device.device_id,
            user_id=employee.id,
            employer_id=owner.id,
            endpoint="https://push.example.test/subscription/active",
            p256dh="C" * 43,
            auth="D" * 22,
            platform="web",
            vapid_public_key="public-key",
        ),
    ])
    db.commit()

    delivered = []
    monkeypatch.setattr(mobile_push_service, "get_or_create_vapid_keypair", lambda: ("private", "public-key"))
    monkeypatch.setattr(mobile_push_service, "_is_public_push_endpoint", lambda endpoint: True)
    monkeypatch.setattr(
        mobile_push_service,
        "webpush",
        lambda **kwargs: delivered.append(kwargs["subscription_info"]["endpoint"]),
    )

    sent = mobile_push_service.send_push_for_alert_types(db, owner.id, ["STOCK_GANTS"])
    assert sent == 1
    assert delivered == ["https://push.example.test/subscription/active"]
