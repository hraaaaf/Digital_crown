"""Run API security regressions with a temporary, explicit nonclinical profile."""
import os
from pathlib import Path
import tempfile
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
import pytest

with tempfile.TemporaryDirectory(prefix="digitalcrown-fue-g04-") as scratch:
    root = Path(scratch)
    env_file = root / ".env"
    env_file.write_text("ENVIRONMENT=test\n", encoding="utf-8")
    for name, folder in (("USER_DATA", "data"), ("CONFIG", "config"), ("RUNTIME", "runtime"), ("LOG", "logs")):
        os.environ["DIGITALCROWN_" + name + "_DIR"] = str(root / folder)
    os.environ["DIGITALCROWN_ENV_FILE"] = str(env_file)
    os.environ["MEDIA_ROOT"] = str(root / "media")
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["CABINET_MASTER_KEY_HEX"] = "00" * 32
    os.environ["SECRET_KEY"] = "fictitious-only-jwt-secret-for-regression-123456"
    for name in ("SQLCIPHER_KEY_HEX", "MOBILE_PAIRING_KEY_HEX"):
        os.environ.pop(name, None)
    result = pytest.main([
        "backend/tests/test_mobile_revocation_epoch.py",
        "backend/tests/test_mobile_credential_hardening.py",
        "backend/tests/test_mobile_identity_security.py",
        "backend/tests/test_mobile_m64_contextual_bridge.py",
        "backend/tests/test_mobile_pocket_security_boundary.py",
        "backend/tests/test_mobile_m6i_passkey.py",
        "-q", "-p", "no:cacheprovider",
    ])
raise SystemExit(result)
