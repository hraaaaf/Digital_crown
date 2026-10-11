"""Fail-closed Windows WeasyPrint native inputs for certified PyInstaller builds.

External binaries are NEVER accepted merely because they are present in MSYS2.
The complete set of 40 source archives and 64 DLLs is matched against one
SHA-pinned provenance manifest. A research-lab manifest is not release approval.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

LAB_PROVENANCE_SHA256 = "3e4389f86361c223e115c4a209e97f59a501798c64fce87e383fda1155beb82e"
LAB_PROVENANCE_HEAD = "2905c55fc5973e3ac7bbbb5a96b27f74fd971909"
# The signed Windows production release must provide an independently approved
# manifest and set this constant via a REVIEWED CODE change and recertification.
# No user-controlled environment variable may override this gate.
RELEASE_APPROVED_PROVENANCE_SHA256: str | None = None

PINNED_FONT_DIGESTS = {
    "DejaVuSans.ttf": "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954",
    "DejaVuSans-Bold.ttf": "e6476c1b80502924294eed40894c5b18e06c181444ca953e5334262df9c27724",
    "LICENSE": "7a083b136e64d064794c3419751e5c7dd10d2f64c108fe5ba161eae5e5958a93",
}
CRITICAL_DLLS = frozenset({
    "libgobject-2.0-0.dll",
    "libpango-1.0-0.dll",
    "libpangoft2-1.0-0.dll",
    "libfontconfig-1.dll",
    "libharfbuzz-0.dll",
})
PANGO_ARCHIVE_SHA256 = "8d86e4a018ff139b010bf357fa1c9f9030fa32ee195c54ed7e89d8ea701851c8"
DEJAVU_ARCHIVE_SHA256 = "dd9fd7bb48ceb0f0f004a4b34d6ac0d9cb4fd2d15273d88780b3cda6cab0beea"


class WindowsNativePdfError(RuntimeError):
    """An unverified or non-approved native dependency MUST stop packaging."""


def _sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def _verified_file(path: Path, expected_sha: str, size: int | None = None) -> Path:
    if path.is_symlink() or not path.is_file():
        raise WindowsNativePdfError(f"Missing/untrusted native PDF file: {path.name}")
    if size is not None and path.stat().st_size != size:
        raise WindowsNativePdfError(f"Native PDF size mismatch: {path.name}")
    if len(expected_sha) != 64 or _sha256(path) != expected_sha:
        raise WindowsNativePdfError(f"Native PDF SHA256 mismatch: {path.name}")
    return path


def _unique_rows(rows: Any, count: int, field: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) != count:
        raise WindowsNativePdfError(f"Incomplete {field} inventory: expected {count}")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise WindowsNativePdfError(f"Malformed {field} entry")
        name = row.get("Name")
        if not isinstance(name, str) or not name or "/" in name or "\\" in name or name in (".", ".."):
            raise WindowsNativePdfError(f"Unsafe {field} entry name")
        key = name.casefold()
        if key in result:
            raise WindowsNativePdfError(f"Duplicate {field}: {name}")
        result[key] = row
    return result


def verify_windows_pdf_sources(
    msys2_root: Path,
    provenance_path: Path,
    *,
    lab_only: bool = False,
    config_path: Path | None = None,
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return PyInstaller binary/data pairs *only* after exact input verification.

    lab_only=True is reserved for an isolated CI discovery check; it MUST NEVER
    be passed by DigitalCrown.spec. Production requires a separately approved
    manifest SHA committed to the certified source.
    """
    expected = LAB_PROVENANCE_SHA256 if lab_only else RELEASE_APPROVED_PROVENANCE_SHA256
    if expected is None:
        raise WindowsNativePdfError("NO-GO: native Windows PDF provenance is not release-approved")
    root = Path(msys2_root)
    provenance = _verified_file(Path(provenance_path), expected)
    try:
        manifest = json.loads(provenance.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError) as exc:
        raise WindowsNativePdfError("Invalid native PDF provenance JSON") from exc
    if not isinstance(manifest, dict):
        raise WindowsNativePdfError("Invalid native PDF provenance object")
    if lab_only:
        if manifest.get("Status") != "EXPERIMENTAL_NOT_RELEASE_APPROVED" or manifest.get("Sha") != LAB_PROVENANCE_HEAD:
            raise WindowsNativePdfError("Lab source SHA/status mismatch")
    else:
        if manifest.get("Status") != "NATIVE_PDF_RELEASE_APPROVED":
            raise WindowsNativePdfError("Native PDF dependencies are not release approved")
    pkgs = _unique_rows(manifest.get("MsYs2Packages"), 40, "MSYS2 packages")
    dlls = _unique_rows(manifest.get("NativeDlls"), 64, "native DLLs")
    if not CRITICAL_DLLS <= set(dlls):
        raise WindowsNativePdfError("Critical WeasyPrint DLL missing from pinned manifest")

    archive_dir = root / "var" / "cache" / "pacman" / "pkg"
    for item in pkgs.values():
        archive_name = item.get("Archive")
        if not isinstance(archive_name, str) or Path(archive_name).name != archive_name:
            raise WindowsNativePdfError("Unsafe MSYS2 archive name")
        _verified_file(archive_dir / archive_name, item["Sha256"], item["Bytes"])
    for pkg, digest in (
        ("mingw-w64-ucrt-x86_64-pango", PANGO_ARCHIVE_SHA256),
        ("mingw-w64-ucrt-x86_64-ttf-dejavu", DEJAVU_ARCHIVE_SHA256),
    ):
        item = pkgs.get(pkg)
        if item is None or item["Sha256"] != digest:
            raise WindowsNativePdfError(f"Official pinned MSYS2 package changed: {pkg}")

    native_dir = root / "ucrt64" / "bin"
    actual = {p.name.casefold() for p in native_dir.glob("*.dll")}
    if actual != set(dlls):
        raise WindowsNativePdfError("MSYS2 native DLL set differs from pinned 64-file manifest")
    binaries: list[tuple[str, str]] = []
    for row in dlls.values():
        filename = row["Name"]
        full = _verified_file(native_dir / filename, row["Sha256"], row["Bytes"])
        binaries.append((str(full), "pdf_native/bin"))

    font_root = root / "ucrt64" / "share"
    datas: list[tuple[str, str]] = []
    for name, digest in PINNED_FONT_DIGESTS.items():
        source = (
            font_root / "licenses" / "ttf-dejavu" / "LICENSE"
            if name == "LICENSE" else font_root / "fonts" / "TTF" / name
        )
        datas.append((str(_verified_file(source, digest)), "pdf_native/fonts"))
    source_cfg = Path(config_path) if config_path is not None else (
        Path(__file__).parent / "windows_fontconfig" / "fonts.conf"
    )
    if not source_cfg.is_file() or source_cfg.is_symlink():
        raise WindowsNativePdfError("Signed Fontconfig configuration missing")
    config = source_cfg.read_text(encoding="utf-8")
    if '<dir prefix="relative">../fonts</dir>' not in config or "/usr/" in config:
        raise WindowsNativePdfError("Fontconfig must resolve fonts from the package")
    datas.extend([
        (str(source_cfg), "pdf_native/fontconfig"),
        (str(provenance), "pdf_native"),
    ])
    return sorted(binaries), sorted(datas)


def verified_windows_pdf_spec_assets() -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Production spec entrypoint; NEVER grants experimental manifest approval."""
    if os.name != "nt":
        return [], []
    msys2 = os.environ.get("DIGITALCROWN_WINDOWS_PDF_MSYS2_ROOT")
    provenance = os.environ.get("DIGITALCROWN_WINDOWS_PDF_PROVENANCE")
    if not msys2 or not provenance:
        raise WindowsNativePdfError("Certified Windows native PDF inputs not provided")
    return verify_windows_pdf_sources(Path(msys2), Path(provenance))
