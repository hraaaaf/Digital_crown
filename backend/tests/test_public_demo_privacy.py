from pathlib import Path


def test_demo_requests_use_platform_user_data_storage():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "public.py"
    ).read_text(encoding="utf-8")
    assert 'AppPaths.get_user_data_dir() / "demo_requests.json"' in source
    assert "os.path.dirname(os.path.dirname(__file__))" not in source


def test_demo_notification_has_no_hardcoded_external_destination():
    source = (
        Path(__file__).resolve().parents[1] / "routers" / "public.py"
    ).read_text(encoding="utf-8")
    assert "contact@digitalcrown.dz" not in source
    assert "settings.ADMIN_NOTIFICATION_EMAIL.strip()" in source
    assert "text=body" in source
    assert "body=body" not in source
