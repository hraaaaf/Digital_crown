from __future__ import annotations

import argparse
import json
import plistlib
import re
import subprocess
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ID = "com.saninova.digitalcrown"
PRIVATE_TRUST_MODE = "signed-manifest+adhoc-codesign-v1"


def require(cond: bool, message: str) -> None:
    if not cond:
        raise SystemExit(message)


def static_contract(root: Path) -> None:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    require(re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version) is not None, "invalid VERSION")
    spec = (root / "DigitalCrown.spec").read_text(encoding="utf-8")
    for snippet in (
        "IS_MACOS = sys.platform == 'darwin'",
        "target_arch='arm64' if IS_MACOS else None",
        "BUNDLE(",
        "bundle_identifier='com.saninova.digitalcrown'",
        "_required('build/macos/DigitalCrown.icns')",
        "backend/macos_private_trust_runtime_hook.py",
        "backend.services.macos_private_trust",
    ):
        require(snippet in spec, f"missing private macOS spec contract: {snippet}")
    for snippet in ("firebase_creds.json", "('.env',", '(\".env\",', "backend/.env"):
        require(snippet not in spec, f"forbidden spec content: {snippet}")

    requirements = (root / "backend" / "requirements-p7-macos.txt").read_text(encoding="utf-8")
    require("pyinstaller==6.16.0" in requirements, "PyInstaller version is not pinned for P7")
    require("-r requirements.txt" in requirements, "P7 must use canonical backend requirements")

    private = (root / "backend" / "services" / "macos_private_trust.py").read_text(encoding="utf-8")
    for snippet in (
        PRIVATE_TRUST_MODE,
        "UPDATE_MACOS_PRIVATE_CODESIGN_VERIFY_FAILED",
        "UPDATE_MACOS_PRIVATE_ADHOC_SIGNATURE_REQUIRED",
        '"Signature=adhoc"',
        'notarization="not_required_private_distribution"',
        'gatekeeper="manual_first_launch_required"',
        "install_private_macos_trust_policy()",
    ):
        require(snippet in private, f"missing private macOS trust contract: {snippet}")
    for forbidden in (
        "Developer ID Application" + ": required",
        "xcrun notarytool submit",
        "xcrun stapler staple",
    ):
        require(forbidden not in private, f"paid Apple dependency leaked into private trust module: {forbidden}")

    hook = (root / "backend" / "macos_private_trust_runtime_hook.py").read_text(encoding="utf-8")
    require("backend.services.macos_private_trust" in hook, "private trust runtime hook missing")

    docs = (root / "docs" / "portability" / "P7_PRIVATE_MACOS_TRUST.md").read_text(encoding="utf-8")
    for snippet in (
        "signed update manifest",
        "exact DMG SHA-256",
        "ad-hoc",
        "not Apple-notarized",
        "clean physical Mac",
    ):
        require(snippet in docs, f"missing private trust documentation contract: {snippet}")

    dmg = (root / "scripts" / "create_macos_dmg.sh").read_text(encoding="utf-8")
    require('ditto "$APP" "$STAGE/DigitalCrown.app"' in dmg, "DMG builder must preserve app via ditto")

    print(f"P7_MACOS_PRIVATE_PACKAGING_CONTRACT=SUCCESS version={version} trust={PRIVATE_TRUST_MODE}")


def _codesign_details(bundle: Path) -> str:
    proc = subprocess.run(
        ["codesign", "-d", "--verbose=4", str(bundle)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    require(proc.returncode == 0, "codesign detail inspection failed:\n" + proc.stdout)
    return proc.stdout


def bundle_contract(root: Path, bundle: Path) -> None:
    require(bundle.is_dir(), f"bundle missing: {bundle}")
    info_path = bundle / "Contents" / "Info.plist"
    exe = bundle / "Contents" / "MacOS" / "DigitalCrown"
    require(info_path.is_file(), "Info.plist missing")
    require(exe.is_file(), "main executable missing")

    info = plistlib.loads(info_path.read_bytes())
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    require(info.get("CFBundleIdentifier") == BUNDLE_ID, "unexpected bundle identifier")
    require(info.get("CFBundleShortVersionString") == version, "bundle short version mismatch")
    require(info.get("CFBundleVersion") == version, "bundle version mismatch")
    require(bool(info.get("NSHighResolutionCapable")), "Retina capability missing")

    archs = subprocess.check_output(["lipo", "-archs", str(exe)], text=True).split()
    require(archs == ["arm64"], f"main executable must be arm64-only, got {archs}")

    verify = subprocess.run(
        ["codesign", "--verify", "--deep", "--strict", "--verbose=4", str(bundle)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    require(verify.returncode == 0, "private codesign verification failed:\n" + verify.stdout)

    details = _codesign_details(bundle)
    require("Signature=adhoc" in details, "bundle must use zero-cost ad-hoc signature")
    require("Authority=Developer ID Application" not in details, "private build must not claim Developer ID")

    forbidden_names = {".env", "firebase_creds.json"}
    leaked = [str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file() and p.name in forbidden_names]
    require(not leaked, f"forbidden secrets in bundle: {leaked}")

    payload = {
        "status": "ok",
        "bundle_identifier": info.get("CFBundleIdentifier"),
        "version": version,
        "archs": archs,
        "trust_mode": PRIVATE_TRUST_MODE,
        "developer_id": False,
        "notarized": False,
        "adhoc_codesign_verified": True,
    }
    print("P7_MACOS_PRIVATE_BUNDLE_CHECK=" + json.dumps(payload, sort_keys=True))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--bundle", type=Path)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    if args.static:
        static_contract(args.root)
    if args.bundle:
        bundle_contract(args.root, args.bundle)
    if not args.static and not args.bundle:
        ap.error("choose --static and/or --bundle")


if __name__ == "__main__":
    main()
