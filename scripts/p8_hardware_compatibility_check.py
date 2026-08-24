from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_JSON = ROOT / "backend" / "hardware_compatibility.json"
MATRIX_MD = ROOT / "docs" / "portability" / "P8_HARDWARE_COMPATIBILITY_MATRIX.md"
ALLOWED_STATUSES = {"SUPPORTED", "LIMITED", "FILE-IMPORT", "UNSUPPORTED"}

REQUIRED_SURFACES = {
    "rvg_intraoral",
    "panoramic_opg",
    "cephalometric_radiograph",
    "dicom",
    "twain_wia_ica",
    "usb_serial_vendor_sdk",
    "mobile_zka_qr_camera",
    "standard_printer",
    "optical_scanner_stl_ply",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    payload = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    require(payload.get("schema") == 1, "P8 matrix schema must be 1")
    require(payload.get("ep_credited") == 0, "Open P8 must not claim EP credit")
    surfaces = {row["id"]: row for row in payload.get("surfaces", [])}
    require(REQUIRED_SURFACES <= surfaces.keys(), f"P8 surfaces missing: {sorted(REQUIRED_SURFACES - surfaces.keys())}")

    for row in surfaces.values():
        for os_key in ("windows", "macos"):
            require(row.get(os_key) in ALLOWED_STATUSES, f"Invalid {os_key} status for {row['id']}")
        if "SUPPORTED" in {row.get("windows"), row.get("macos")}:
            require(bool(row.get("real_device_test_evidence")), f"{row['id']} claims SUPPORTED without real-device evidence")

    for surface_id in ("rvg_intraoral", "panoramic_opg", "cephalometric_radiograph"):
        row = surfaces[surface_id]
        require(row["windows"] == "FILE-IMPORT" and row["macos"] == "FILE-IMPORT", f"{surface_id} file-first contract changed")
        require(row["direct_acquisition"] == "UNSUPPORTED", f"{surface_id} direct acquisition claim requires device proof")

    require(surfaces["dicom"]["windows"] == "UNSUPPORTED" and surfaces["dicom"]["macos"] == "UNSUPPORTED", "DICOM claim changed without proof")
    require(surfaces["mobile_zka_qr_camera"]["windows"] == "LIMITED", "QR camera must remain conservative without real-device OS proof")
    require(surfaces["mobile_zka_qr_camera"]["macos"] == "LIMITED", "QR camera must remain conservative without real-device OS proof")

    requirements = (ROOT / "backend" / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependency in ("pydicom", "pyserial", "pyusb", "pytwain", "twain"):
        require(
            not re.search(rf"(?m)^\s*{re.escape(dependency)}(?:\[.*?\])?\s*(?:[=<>!~]|$)", requirements),
            f"Direct hardware dependency {dependency!r} added: update P8 matrix and attach device proof.",
        )

    for path in (ROOT / "frontend" / "src").rglob("*"):
        if not path.is_file() or path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for marker in ("navigator.usb", "navigator.serial"):
            require(
                marker not in text,
                f"Direct browser hardware API {marker!r} found in {path.relative_to(ROOT)}: update P8 matrix and attach device proof.",
            )

    rvg = (ROOT / "backend" / "schemas" / "rvg.py").read_text(encoding="utf-8")
    for mime in ("image/jpeg", "image/png", "image/webp", "application/pdf"):
        require(mime in rvg, f"RVG MIME contract changed: {mime} missing")

    modal = (ROOT / "frontend" / "src" / "features" / "patients" / "components" / "RvgUploadModal.tsx").read_text(encoding="utf-8")
    require('accept="image/jpeg,image/png,image/webp,application/pdf"' in modal, "RVG frontend file-import contract changed")

    ia = (ROOT / "backend" / "routers" / "ia.py").read_text(encoding="utf-8")
    require('@router.post("/upload-radio")' in ia, "cephalo file-import route missing")
    require('@router.post("/upload-panoramic")' in ia, "panoramic file-import route missing")
    require("UploadFile" in ia, "imaging UploadFile contract missing")

    pano = (ROOT / "frontend" / "src" / "features" / "panoramic" / "PanoramicStudio.tsx").read_text(encoding="utf-8")
    require('accept="image/*"' in pano, "panoramic frontend file-import contract changed")

    ceph = (ROOT / "frontend" / "src" / "features" / "ortho" / "components" / "Step1Cephalo.tsx").read_text(encoding="utf-8")
    require('accept="image/*"' in ceph, "cephalo frontend file-import contract changed")
    require("type.startsWith('image/')" in ceph, "cephalo frontend image gate missing")

    scanner = (ROOT / "frontend" / "src" / "features" / "mobile" / "Onboarding" / "OnboardingScanner.tsx").read_text(encoding="utf-8")
    require("Html5QrcodeScanner" in scanner, "mobile QR camera contract missing")
    require("window.isSecureContext" in scanner, "mobile QR secure-context gate missing")

    md = MATRIX_MD.read_text(encoding="utf-8")
    require("**0 EP credited.**" in md, "P8 markdown must remain explicit about zero EP credit")
    require("Mobile/browser camera for ZKA pairing | LIMITED | LIMITED" in md, "P8 markdown QR status drifted from JSON")

    print("P8_HARDWARE_COMPATIBILITY_CONTRACT=SUCCESS")


if __name__ == "__main__":
    main()
