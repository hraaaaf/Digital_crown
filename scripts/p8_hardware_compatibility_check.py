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
    "clinical_intraoral_camera",
    "standard_printer",
    "optical_scanner_stl_ply",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    payload = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    require(payload.get("schema") == 1, "P8 matrix schema must be 1")
    require(payload.get("status") == "closed-certified-boundary", "P8 matrix must expose certified boundary status")
    require(payload.get("ep_credited") == 21, "Closed P8 must credit exactly 21 EP")

    rows = payload.get("surfaces", [])
    ids = [row.get("id") for row in rows]
    require(len(ids) == len(set(ids)), "P8 surface ids must be unique")
    surfaces = {row["id"]: row for row in rows}
    require(
        REQUIRED_SURFACES <= surfaces.keys(),
        f"P8 surfaces missing: {sorted(REQUIRED_SURFACES - surfaces.keys())}",
    )

    for row in surfaces.values():
        require(bool(row.get("evidence")), f"{row['id']} must carry repository evidence")
        for os_key in ("windows", "macos"):
            require(row.get(os_key) in ALLOWED_STATUSES, f"Invalid {os_key} status for {row['id']}")
        statuses = {row.get("windows"), row.get("macos")}
        if "SUPPORTED" in statuses:
            require(
                bool(row.get("real_device_test_evidence")),
                f"{row['id']} claims SUPPORTED without real-device evidence",
            )
            require(
                row.get("direct_acquisition") != "UNSUPPORTED",
                f"{row['id']} claims SUPPORTED while direct acquisition is UNSUPPORTED",
            )
        if "LIMITED" in statuses:
            require(bool(row.get("limitations")), f"{row['id']} claims LIMITED without explicit limitations")
        if "FILE-IMPORT" in statuses:
            require(bool(row.get("formats")), f"{row['id']} claims FILE-IMPORT without format contract")

    for surface_id in (
        "rvg_intraoral",
        "panoramic_opg",
        "cephalometric_radiograph",
        "clinical_intraoral_camera",
    ):
        row = surfaces[surface_id]
        require(
            row["windows"] == "FILE-IMPORT" and row["macos"] == "FILE-IMPORT",
            f"{surface_id} file-first contract changed",
        )
        require(
            row["direct_acquisition"] == "UNSUPPORTED",
            f"{surface_id} direct acquisition claim requires device proof",
        )

    for surface_id in ("dicom", "twain_wia_ica", "usb_serial_vendor_sdk", "optical_scanner_stl_ply"):
        row = surfaces[surface_id]
        require(
            row["windows"] == "UNSUPPORTED" and row["macos"] == "UNSUPPORTED",
            f"{surface_id} support claim changed without proof",
        )

    qr = surfaces["mobile_zka_qr_camera"]
    require(qr["windows"] == "LIMITED" and qr["macos"] == "LIMITED", "QR camera must remain LIMITED without OS-specific device proof")
    require(qr["direct_acquisition"] == "QR_PAIRING_ONLY", "QR camera scope drifted beyond pairing")

    printer = surfaces["standard_printer"]
    require(printer["windows"] == "LIMITED" and printer["macos"] == "LIMITED", "Printer support must remain OS-mediated LIMITED")
    require(printer["direct_acquisition"] == "OS_MEDIATED_ONLY", "Printer device-management claim changed")

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
    require(
        'accept="image/jpeg,image/png,image/webp,application/pdf"' in modal,
        "RVG frontend file-import contract changed",
    )

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
    for marker in (
        "**Status:** CLOSED ✅ — **21 EP**",
        "No direct dental device is certified as `SUPPORTED`",
        "future promotion to `SUPPORTED`",
    ):
        require(marker in md, f"P8 closeout marker missing: {marker}")
    require(
        "Mobile/browser camera for ZKA pairing | LIMITED | LIMITED" in md,
        "P8 markdown QR status drifted from JSON",
    )

    print("P8_HARDWARE_COMPATIBILITY_CONTRACT=SUCCESS status=CLOSED ep=21 supported_direct_devices=0")


if __name__ == "__main__":
    main()
