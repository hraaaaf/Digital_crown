"""PyInstaller early hook: verify pinned Windows PDF files before any backend import.

The installed cabinet may not use GTK/Pango from the host machine. Keep this
dependency gate independent of backend/__init__.py and its DB/model imports.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

# Must be changed in lockstep with the independently certified provenance
# inside backend/windows_native_pdf_bundle.py. Lab proofs are NEVER accepted.
RELEASE_APPROVED_PROVENANCE_SHA256 = None


def _sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _verified(path, digest, size=None):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("FUE-G04 missing/untrusted packaged PDF asset: " + path.name)
    if size is not None and path.stat().st_size != size:
        raise RuntimeError("FUE-G04 packaged PDF size mismatch: " + path.name)
    if _sha256(path) != digest:
        raise RuntimeError("FUE-G04 packaged PDF SHA mismatch: " + path.name)


if os.name == "nt":
    if not getattr(sys, "frozen", False) or not getattr(sys, "_MEIPASS", None):
        raise RuntimeError("FUE-G04 native PDF runtime requires certified frozen Windows executable")
    if RELEASE_APPROVED_PROVENANCE_SHA256 is None:
        raise RuntimeError("FUE-G04 NO-GO: unapproved native PDF provenance")

    base = Path(sys._MEIPASS).resolve()
    native = base / "pdf_native"
    manifest_path = native / "FUE-G04-experimental-complete-provenance.json"
    _verified(manifest_path, RELEASE_APPROVED_PROVENANCE_SHA256)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("Status") != "NATIVE_PDF_RELEASE_APPROVED":
        raise RuntimeError("FUE-G04 native PDF provenance not release approved")
    binaries = manifest.get("NativeDlls")
    if not isinstance(binaries, list) or len(binaries) != 64:
        raise RuntimeError("FUE-G04 incorrect native DLL manifest")
    expected_names = set()
    for entry in binaries:
        name = entry["Name"]
        if not isinstance(name, str) or not name.lower().endswith(".dll"):
            raise RuntimeError("FUE-G04 invalid DLL inventory name")
        if "/" in name or "\\" in name or name in expected_names:
            raise RuntimeError("FUE-G04 unsafe/duplicated DLL inventory name")
        expected_names.add(name)
        _verified(native / "bin" / name, entry["Sha256"], entry["Bytes"])
        # PyInstaller auto-hooks may independently copy these DLLs at _internal.
        # Every such copy must be byte-identical to the approved source.
        extra = base / name
        if extra.is_file():
            _verified(extra, entry["Sha256"], entry["Bytes"])
    if {p.name for p in (native / "bin").glob("*.dll")} != expected_names:
        raise RuntimeError("FUE-G04 extra/missing bundled native DLL")

    fonts = native / "fonts"
    for name, digest in {
        "DejaVuSans.ttf": "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954",
        "DejaVuSans-Bold.ttf": "e6476c1b80502924294eed40894c5b18e06c181444ca953e5334262df9c27724",
        "LICENSE": "7a083b136e64d064794c3419751e5c7dd10d2f64c108fe5ba161eae5e5958a93",
    }.items():
        _verified(fonts / name, digest)
    config = native / "fontconfig" / "fonts.conf"
    _verified(config, "65247abfac13b2e4a8e1b70c879ff69ea9a26df0ceaa3db4eab758a72c5c8a13")
    if '<dir prefix="relative">../fonts</dir>' not in config.read_text(encoding="utf-8"):
        raise RuntimeError("FUE-G04 Fontconfig cannot resolve packaged fonts")
    os.environ["WEASYPRINT_DLL_DIRECTORIES"] = str(native / "bin")
    os.environ["FONTCONFIG_FILE"] = str(config)
    os.environ["FONTCONFIG_PATH"] = str(config.parent)
