from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_macos_frozen_spec_loads_private_trust_runtime_hook():
    spec = (ROOT / "DigitalCrown.spec").read_text(encoding="utf-8")
    assert "if IS_MACOS:" in spec
    assert "backend/macos_private_trust_runtime_hook.py" in spec
    assert "runtime_hooks=runtime_hooks" in spec


def test_private_runtime_hook_installs_private_policy():
    hook = (ROOT / "backend" / "macos_private_trust_runtime_hook.py").read_text(encoding="utf-8").strip()
    assert hook == "import backend.services.macos_private_trust"

    policy = (ROOT / "backend" / "services" / "macos_private_trust.py").read_text(encoding="utf-8")
    assert 'PRIVATE_TRUST_MODE = "signed-manifest+adhoc-codesign-v1"' in policy
    assert "Signature=adhoc" in policy
    assert "UPDATE_MACOS_PRIVATE_ADHOC_SIGNATURE_REQUIRED" in policy
    assert "MacOSUpdateApplyService._verify_macos_distribution = classmethod(_verify_private_distribution)" in policy
    assert "install_private_macos_trust_policy()" in policy
    assert "install_private_macos_rescue_preflight()" in policy
