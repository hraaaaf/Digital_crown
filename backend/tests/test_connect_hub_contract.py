from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ROUTER = ROOT / "backend" / "routers" / "connect_hub.py"
REQUIREMENTS = ROOT / "backend" / "requirements.txt"
MOBILE_PUSH = ROOT / "backend" / "routers" / "mobile_push.py"


def test_connect_hub_is_read_only_and_has_no_duplicate_persistence():
    source = ROUTER.read_text(encoding="utf-8")

    assert '@router.get("/connect-hub")' in source
    assert "db.add(" not in source
    assert "db.commit(" not in source
    assert "db.delete(" not in source
    assert "connect_hub_notifications" not in source
    assert "DeviceToken" not in source
    assert "webpush(" not in source
    assert "send_sms" not in source
    assert "send_whatsapp" not in source


def test_connect_hub_preserves_canonical_permission_and_tenant_boundaries():
    source = ROUTER.read_text(encoding="utf-8")

    assert 'has_permission(current_user, "patients")' in source
    assert 'has_permission(current_user, ["accounting", "payments"])' in source
    assert "models.ProactiveAlert.employer_id == employer_id" in source
    assert "models.Patient.deleted_at.is_(None)" in source
    assert "accounting_service.get_treasury_summary" in source


def test_connect_hub_never_overclaims_delivery():
    source = ROUTER.read_text(encoding="utf-8")

    assert source.count('"delivery_verified": False') >= 2
    assert '"delivery_semantics": "source_state_only"' in source
    assert '"delivery_state": "source_state"' in source


def test_legacy_fcm_registration_stays_disabled_and_no_fcm_runtime_dependency_exists():
    push_source = MOBILE_PUSH.read_text(encoding="utf-8")
    requirements = REQUIREMENTS.read_text(encoding="utf-8").lower()

    assert "_disable_legacy_fcm_registration_route()" in push_source
    assert "firebase-admin" not in requirements
    assert "pywebpush" in requirements
