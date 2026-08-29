import plistlib
from pathlib import Path

import pytest

from backend.services.macos_private_trust import PRIVATE_TRUST_MODE
from backend.services.macos_update_apply import MacOSUpdateApplyService
from backend.services.update_engine import UpdatePreparationError


def _app(tmp_path: Path, version: str = "1.0.1") -> Path:
    app = tmp_path / "DigitalCrown.app"
    exe = app / "Contents" / "MacOS" / "DigitalCrown"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"binary")
    (app / "Contents" / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.saninova.digitalcrown",
                "CFBundleShortVersionString": version,
            }
        )
    )
    return app


def test_private_trust_accepts_only_verified_adhoc_bundle(monkeypatch, tmp_path):
    app = _app(tmp_path)
    calls = []

    def fake_run(args, error_code, timeout=120.0):
        calls.append((args, error_code))
        if "-d" in args:
            return "Executable=/tmp/DigitalCrown\nIdentifier=com.saninova.digitalcrown\nSignature=adhoc\n"
        return "valid on disk\nsatisfies its Designated Requirement\n"

    monkeypatch.setattr(MacOSUpdateApplyService, "_run_checked", staticmethod(fake_run))
    proof = MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")
    assert proof["trust_mode"] == PRIVATE_TRUST_MODE
    assert proof["private_codesign"] == "adhoc_valid"
    assert proof["developer_id"] == "not_required_private_distribution"
    assert any("--verify" in args for args, _ in calls)


def test_private_trust_rejects_unsigned_or_identity_signed_bundle(monkeypatch, tmp_path):
    app = _app(tmp_path)

    def fake_run(args, error_code, timeout=120.0):
        if "-d" in args:
            return "Identifier=com.saninova.digitalcrown\nSignature=Developer ID Application: Someone\n"
        return "ok"

    monkeypatch.setattr(MacOSUpdateApplyService, "_run_checked", staticmethod(fake_run))
    with pytest.raises(UpdatePreparationError, match="PRIVATE_ADHOC_SIGNATURE_REQUIRED"):
        MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")


def test_private_trust_rejects_wrong_bundle_or_version(monkeypatch, tmp_path):
    app = _app(tmp_path, version="1.0.0")
    monkeypatch.setattr(MacOSUpdateApplyService, "_run_checked", staticmethod(lambda *a, **k: "Signature=adhoc"))
    with pytest.raises(UpdatePreparationError, match="BUNDLE_VERSION_MISMATCH"):
        MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")

    info = app / "Contents" / "Info.plist"
    info.write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.example.wrong",
                "CFBundleShortVersionString": "1.0.1",
            }
        )
    )
    with pytest.raises(UpdatePreparationError, match="BUNDLE_ID_MISMATCH"):
        MacOSUpdateApplyService._verify_app_bundle(app, expected_version="1.0.1")
