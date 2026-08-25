from pathlib import Path
import json
from types import SimpleNamespace

import pytest

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
