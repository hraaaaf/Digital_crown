from __future__ import annotations

import argparse
import json
import plistlib
import re
import subprocess
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ID = "com.saninova.digitalcrown"


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
        "macos/DigitalCrown.entitlements",
    ):
        require(snippet in spec, f"missing macOS spec contract: {snippet}")
    for snippet in ("firebase_creds.json", "('.env',", '(\".env\",', "backend/.env"):
        require(snippet not in spec, f"forbidden spec content: {snippet}")

    entitlements = plistlib.loads((root / "macos" / "DigitalCrown.entitlements").read_bytes())
    require(entitlements == {}, "P7 entitlements must start least-privilege/empty")

    requirements = (root / "backend" / "requirements-p7-macos.txt").read_text(encoding="utf-8")
    require("pyinstaller==6.16.0" in requirements, "PyInstaller version is not pinned for P7")
    require("-r backend/requirements.txt" in requirements, "P7 must use canonical backend requirements")

    dmg = (root / "scripts" / "create_macos_dmg.sh").read_text(encoding="utf-8")
    require('ditto "$APP" "$STAGE/DigitalCrown.app"' in dmg, "DMG builder must preserve signed app via ditto")

    print(f"P7_MACOS_PACKAGING_CONTRACT=SUCCESS version={version}")


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
    require(verify.returncode == 0, "codesign verification failed:\n" + verify.stdout)

    details = _codesign_details(bundle)
    require("Authority=Developer ID Application" in details, "bundle is not Developer ID signed")
    require(re.search(r"flags=0x[0-9a-fA-F]+\(runtime\)", details) is not None, "Hardened Runtime flag missing")

    forbidden_names = {".env", "firebase_creds.json"}
    leaked = [str(p.relative_to(bundle)) for p in bundle.rglob("*") if p.is_file() and p.name in forbidden_names]
    require(not leaked, f"forbidden secrets in bundle: {leaked}")

    payload = {
        "status": "ok",
        "bundle_identifier": info.get("CFBundleIdentifier"),
        "version": version,
        "archs": archs,
        "developer_id": True,
        "hardened_runtime": True,
        "codesign_verified": True,
    }
    print("P7_MACOS_BUNDLE_CHECK=" + json.dumps(payload, sort_keys=True))


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
