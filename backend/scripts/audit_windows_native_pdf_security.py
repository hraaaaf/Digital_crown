"""FUE-G04: conservative MSYS2 ownership, license and PE import audit.

Development evidence only. A PASS is NOT legal release approval or a complete
(dynamic LoadLibrary) dependency closure. Does not build/install a cabinet app.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path


def _run(argv: list[str]) -> str:
    result = subprocess.run(argv, capture_output=True, text=True, errors="replace",
                            timeout=45, check=False)
    if result.returncode:
        raise RuntimeError(f"Native provenance command failed: {argv[1:3]} (exit {result.returncode})")
    return result.stdout.strip()


def _field(info: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}\s*:\s*(.*?)\s*$", info, re.MULTILINE | re.IGNORECASE)
    if not match or not match.group(1):
        raise RuntimeError(f"Missing pacman metadata field {key}")
    return match.group(1)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _basename(name: str) -> str:
    if not name or not re.fullmatch(r"[A-Za-z0-9_.+-]+", name):
        raise RuntimeError("Unsafe PE imported library name")
    if not name.casefold().endswith(".dll"):
        raise RuntimeError(f"Imported library is not a DLL: {name}")
    return name.casefold()


def classify_import(name: str, bundled: set[str], system32: Path) -> str:
    """Fail-closed if an import is neither pinned nor on the Windows system."""
    name = _basename(name)
    if name in bundled:
        return "pinned_bundle"
    if name.startswith(("api-ms-win-", "ext-ms-")):
        return "windows_api_set"
    if (system32 / name).is_file():
        return "windows_system32"
    raise RuntimeError(f"Unresolved non-bundled native DLL import: {name}")


def inspect_pe(path: Path, bundled: set[str], system32: Path) -> list[dict]:
    try:
        import pefile  # installed and pinned only by ephemeral audit CI
    except ImportError as exc:
        raise RuntimeError("pefile audit dependency is required") from exc
    pe = pefile.PE(str(path), fast_load=True)
    try:
        if pe.FILE_HEADER.Machine != 0x8664:
            raise RuntimeError(f"Not an AMD64 PE DLL: {path.name}")
        dirs = pefile.DIRECTORY_ENTRY
        pe.parse_data_directories(directories=[
            dirs["IMAGE_DIRECTORY_ENTRY_IMPORT"],
            dirs["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"],
        ])
        result = []
        for key in ("DIRECTORY_ENTRY_IMPORT", "DIRECTORY_ENTRY_DELAY_IMPORT"):
            for value in getattr(pe, key, []):
                if not value.dll:
                    raise RuntimeError(f"PE import lacks DLL name: {path.name}")
                imported = value.dll.decode("ascii", errors="strict")
                result.append({
                    "import": _basename(imported),
                    "category": classify_import(imported, bundled, system32),
                    "delay_load": key == "DIRECTORY_ENTRY_DELAY_IMPORT",
                })
        return sorted(result, key=lambda x: (x["import"], x["delay_load"]))
    finally:
        pe.close()


def audit(msys_root: Path, provenance: Path, report_path: Path) -> dict:
    if os.name != "nt":
        raise RuntimeError("PE/ownership provenance audit requires real Windows")
    spec = importlib.util.spec_from_file_location(
        "fue_g04_verified_native_bundle",
        Path(__file__).resolve().parents[1] / "windows_native_pdf_bundle.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing official candidate source verifier")
    import sys
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    dll_pairs, _ = module.verify_windows_pdf_sources(msys_root, provenance, lab_only=True)
    expected = json.loads(provenance.read_text(encoding="utf-8"))
    if expected["Sha"] != module.LAB_PROVENANCE_HEAD:
        raise RuntimeError("Provenance source run mismatch")
    pdir = msys_root / "usr" / "bin"
    pacman = str(pdir / "pacman.exe")
    pacconf = str(pdir / "pacman-conf.exe")
    if not Path(pacman).is_file() or not Path(pacconf).is_file():
        raise RuntimeError("Missing MSYS2 package-manager binaries")
    siglevel = _run([pacconf, "SigLevel"])
    if "Required" not in siglevel:
        raise RuntimeError("MSYS2 pacman signature policy is not required")
    packages = {}
    allowed = {row["Name"].casefold() for row in expected["MsYs2Packages"]}
    all_licenses = set()
    for row in expected["MsYs2Packages"]:
        name = row["Name"]
        meta = _run([pacman, "-Qi", name])
        installed_version = _field(meta, "Version")
        license_line = _field(meta, "Licenses")
        if installed_version != row["Version"]:
            raise RuntimeError(f"MSYS2 installed package version changed: {name}")
        archived = msys_root / "var" / "cache" / "pacman" / "pkg" / row["Archive"]
        disk_meta = _run([pacman, "-Qip", str(archived)])
        if (_field(disk_meta, "Name") != name or
                _field(disk_meta, "Version") != row["Version"]):
            raise RuntimeError(f"MSYS2 archive provenance metadata differs: {name}")
        archived_licenses = _field(disk_meta, "Licenses")
        if license_line != archived_licenses:
            raise RuntimeError(f"MSYS2 archive license metadata differs: {name}")
        paths = _run([pacman, "-Qlq", name]).splitlines()
        notice_files = []
        for raw in paths:
            normalized = raw.replace("\\", "/")
            if "/share/licenses/" not in normalized or normalized.endswith("/"):
                continue
            if normalized.startswith("/ucrt64/"):
                full = msys_root / normalized.removeprefix("/")
            elif re.match(r"^[A-Za-z]:/", normalized):
                full = Path(normalized)
            else:
                raise RuntimeError(f"MSYS2 license notice outside UCRT64: {name}")
            if not full.is_file() or full.is_symlink():
                raise RuntimeError(f"Missing linked license notice in {name}")
            notice_files.append({
                "path": normalized.split("/ucrt64/", 1)[-1],
                "sha256": _sha256(full),
                "bytes": full.stat().st_size,
            })
        packages[name] = {
            "version": installed_version,
            "license_metadata": license_line,
            "license_files": sorted(notice_files, key=lambda x: x["path"]),
            "source_archive_sha256": row["Sha256"],
        }
        all_licenses.add(license_line)

    system32 = Path(os.environ["WINDIR"]) / "System32"
    dll_entries = {}
    set_native = {Path(source).name.casefold() for source, _ in dll_pairs}
    for source, _ in dll_pairs:
        path = Path(source)
        # pacman owns POSIX MSYS2 paths; the Windows host Python supplies
        # drive-letter paths that pacman -Qo cannot resolve reliably.
        posix_path = "/ucrt64/bin/" + path.name
        owner = _run([pacman, "-Qo", "-q", posix_path])
        if owner.casefold() not in allowed:
            raise RuntimeError(f"Native DLL not owned by pinned MSYS2 package: {path.name}")
        imports = inspect_pe(path, set_native, system32)
        dll_entries[path.name] = {
            "sha256": _sha256(path),
            "package": owner,
            "imports": imports,
        }
    evidence = {
        "status": "EXPERIMENTAL_NATIVE_SECURITY_AUDIT_ONLY",
        "source_commit": expected["Sha"],
        "provenance_sha256": _sha256(provenance),
        "package_signature_policy": siglevel,
        "all_pkg_count": len(packages),
        "native_dll_count": len(dll_entries),
        "package_licenses": packages,
        "native_dll_provenance": dll_entries,
        "caveats": [
            "Static PE imports and delay imports only; dynamic LoadLibrary not covered",
            "Pacman installed-package policy alone is not an independently verified redistribution signature",
            "License metadata and notices are an inventory, not legal redistribution approval",
            "No production DigitalCrown.exe or certified installer was created, started or approved",
            "Python wheels and source-build reproduction need separate promotion controls",
        ],
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    print(f"FUE_G04_AUDITED_PACKAGES={len(packages)}")
    print(f"FUE_G04_AUDITED_PE_DLLS={len(dll_entries)}")
    print("FUE_G04_STATIC_PE_IMPORT_RESOLUTION=PASS")
    print("FUE_G04_LICENSE_INVENTORY=CAPTURED_NOT_LEGAL_APPROVAL")
    print("FUE_G04_NATIVE_RELEASE_GATE=NO_GO")
    return evidence


def main() -> None:
    arg = argparse.ArgumentParser()
    arg.add_argument("--msys2-root", type=Path, required=True)
    arg.add_argument("--provenance", type=Path, required=True)
    arg.add_argument("--report", type=Path, required=True)
    inputs = arg.parse_args()
    audit(inputs.msys2_root, inputs.provenance, inputs.report)


if __name__ == "__main__":
    main()
