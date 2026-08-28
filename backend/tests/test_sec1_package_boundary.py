import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "DigitalCrown.spec"
BUILD_SCRIPT = ROOT / "scripts" / "build_exe.py"
PRIVATE_KEY_ASSIGNMENT = re.compile(
    r"DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL\s*=\s*['\"][A-Za-z0-9_-]{20,}['\"]"
)
PEM_PRIVATE_MARKERS = (
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN ED25519 PRIVATE KEY-----",
)


def _iter_distributed_source_files():
    for base in (ROOT / "backend", ROOT / "frontend" / "src"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            # backend/tests are not imported by the packaged runtime. Excluding
            # them also prevents the detector from flagging its own test markers.
            if "tests" in path.relative_to(ROOT).parts:
                continue
            if path.is_file() and path.suffix.lower() in {".py", ".ts", ".tsx", ".js", ".json"}:
                yield path


def test_pyinstaller_does_not_bundle_env_or_control_plane_credentials():
    spec = SPEC.read_text(encoding="utf-8")
    build_script = BUILD_SCRIPT.read_text(encoding="utf-8")

    # Comments mentioning .env are fine; a datas tuple that includes it is not.
    assert re.search(r"\(\s*['\"]\.env(?:\.local)?['\"]\s*,", spec) is None
    assert "firebase_creds.json" not in spec
    assert "DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL" not in spec

    # The legacy helper is also a valid build entrypoint. It must obey the same
    # boundary instead of conditionally copying a local Firebase service account.
    assert "firebase_creds.json" not in build_script
    assert "DIGITALCROWN_LICENSE_SIGNING_PRIVATE_KEY_B64URL" not in build_script
    assert "--add-data" in build_script


def test_firebase_service_account_is_not_tracked_in_client_tree():
    assert not (ROOT / "backend" / "core" / "firebase_creds.json").exists()


def test_distributed_sources_contain_no_literal_private_signing_key():
    offenders = []
    for path in _iter_distributed_source_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PRIVATE_KEY_ASSIGNMENT.search(text) or any(marker in text for marker in PEM_PRIVATE_MARKERS):
            offenders.append(str(path.relative_to(ROOT)))

    assert offenders == [], f"Private signing material found in distributed sources: {offenders}"
