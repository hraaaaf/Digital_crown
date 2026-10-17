"""SEC-P1.4 repository-state guard; no runtime changes and no secrets.

This is deliberately a narrow static guard, not a certification scanner for
every secret in the existing public repository.
"""
from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]

EXPERIMENTAL_FILES = (
    "scripts/security/sec_p1_4_signed_license_reference.py",
    "scripts/security/test_sec_p1_4_signed_license_reference.py",
    "scripts/security/sec_p1_4_architecture_guards.py",
    "docs/security/SEC_P1_4_SIGNED_LICENSE_PACKAGING_ADR.md",
    ".github/workflows/sec-p1-4-signed-license-lab.yml",
)


def main() -> None:
    for relative in EXPERIMENTAL_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise AssertionError(f"Missing experimental file: {relative}")
        content = path.read_text("utf-8")
        # Construct markers rather than spelling the whole PEM header here:
        # otherwise the guard falsely flags its own detection rules.
        pem_prefix = "-----" + "BEGIN "
        for key_kind in ("PRIVATE KEY", "OPENSSH PRIVATE KEY",
                         "EC PRIVATE KEY", "RSA PRIVATE KEY"):
            if pem_prefix + key_kind + "-----" in content:
                raise AssertionError(f"Private key in SEC-P1.4 experiment file: {relative}")
        if relative.endswith(".py"):
            ast.parse(content, filename=relative)

    spec = (ROOT / "DigitalCrown.spec").read_text("utf-8")
    launcher = (ROOT / "run.py").read_text("utf-8")
    if "verify_installable_release_directory" not in spec:
        raise AssertionError("Commercial EXE certification gate changed")
    if "verify_installable_release_identity" not in launcher:
        raise AssertionError("Frozen runtime certification gate changed")
    if not (ROOT / "backend/services/license_service.py").is_file():
        raise AssertionError("Existing licensing service missing")
    if not (ROOT / "scripts/build_exe.py").is_file():
        raise AssertionError("Legacy builder is missing; inspect independently")

    # The reference must not be silently imported into backend product code.
    for path in (ROOT / "backend").rglob("*.py"):
        if "sec_p1_4_signed_license_reference" in path.read_text("utf-8"):
            raise AssertionError(f"Experimental verifier leaked into production: {path}")

    legacy = (ROOT / "scripts/build_exe.py").read_text("utf-8")
    if "firebase_creds.json" in legacy:
        print("SEC_P1_4_LEGACY_BUILDER_CREDENTIAL_RISK=OPEN")
    else:
        print("SEC_P1_4_LEGACY_BUILDER_CREDENTIAL_RISK=REVIEW_REQUIRED")

    print("SEC_P1_4_RELEASE_GATES=UNCHANGED")
    print("SEC_P1_4_RUNTIME_LICENSING_SWITCHED=NO")
    print("SEC_P1_4_PRIVATE_SIGNING_KEY_IN_EXPERIMENT=NO")
    print("SEC_P1_4_PRODUCTION_DATA_USED=NO")


if __name__ == "__main__":
    main()
