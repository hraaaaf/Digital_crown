"""Private, fail-closed staging of authentic FACAD Robert export evidence.

NO FACAD runtime, trial activation, patient data, decompilation, numeric parity,
or modification of the canonical repository manifest. The resulting directory
is private and MUST NOT be committed or uploaded to public CI.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from audit.cephalo_lot08_facad_parity_validate import (
    DEFAULT_MANIFEST, ROOT, validate_manifest,
)

ROBERT_SHA256 = "67a81ad8d2c2489ffe84a1dfbbb897761ae855ece4ebf948c12af232562ec089"
VERSION = "3.14.1.1111"
TARGETS = {
    "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": "32F",
    "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": "13F",
}
MENUS = {
    "ANALYSIS_VALUES": "Analysis Values",
    "ANALYSIS_PROPERTIES": "Analysis Properties",
    "MARKER_POSITIONS": "Object Values",
}
ROOT_KEYS = {
    "official_robert_sha256", "facad_version", "same_trace_case_id",
    "authorized_facad_use_confirmed", "same_lateral_tracing_confirmed",
    "exports",
}
ENTRY_KEYS = {
    "profile_target_id", "artifact_kind", "file", "observed_at",
    "vendor_menu", "marker_positions_content_verified",
}
MAX_EXPORT_BYTES = 20_000_000


def _require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError(reason)


def _local_file(base: Path, value: object) -> Path:
    _require(isinstance(value, str) and bool(value), "source file path missing")
    _require("\\" not in value and ":" not in value, "source path must use relative forward slashes")
    raw = PurePosixPath(value)
    _require(not raw.is_absolute() and ".." not in raw.parts and raw.parts != (".",),
             "source file path must remain inside private intake directory")
    path = base.joinpath(*raw.parts)
    for component in [path, *path.parents]:
        if component == base.parent:
            break
        _require(not component.is_symlink(), "source symlink not allowed")
    src = path.resolve(strict=True)
    _require(src.is_relative_to(base) and src.is_file(), "source must be a file in private intake directory")
    size = src.stat().st_size
    _require(0 < size <= MAX_EXPORT_BYTES, "empty or oversized FACAD export")
    return src


def _checked_input(intake_path: Path) -> tuple[dict, list[dict]]:
    path = intake_path.resolve(strict=True)
    _require(not path.is_relative_to(ROOT.resolve()),
             "private intake must be OUTSIDE the Git repository")
    _require(path.is_file(), "intake JSON must be a local file")
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict) and set(data) == ROOT_KEYS, "intake keys mismatch; no extra secrets accepted")
    _require(data["official_robert_sha256"] == ROBERT_SHA256, "official Robert source hash mismatch")
    _require(data["facad_version"] == VERSION, "version must match pinned FACAD 3.14.1.1111")
    opaque = data["same_trace_case_id"]
    _require(isinstance(opaque, str) and re.fullmatch(r"[A-Za-z0-9_-]{8,64}", opaque) is not None,
             "same_trace_case_id must be opaque, 8-64 letters/digits/_/-")
    _require(data["authorized_facad_use_confirmed"] is True, "FACAD rights not confirmed; stop")
    _require(data["same_lateral_tracing_confirmed"] is True, "same tracing unconfirmed; stop")
    entries = data["exports"]
    _require(isinstance(entries, list) and len(entries) == 6, "exactly 6 authentic export files required")
    observed = set()
    source_files = set()
    normalized = []
    for entry in entries:
        _require(isinstance(entry, dict) and set(entry) == ENTRY_KEYS, "export record keys mismatch")
        profile, kind = entry["profile_target_id"], entry["artifact_kind"]
        _require(profile in TARGETS and kind in MENUS, "unexpected profile or export kind")
        pair = (profile, kind)
        _require(pair not in observed, "duplicate profile/export family")
        observed.add(pair)
        _require(entry["vendor_menu"] == MENUS[kind], "actual FACAD 3.14 vendor menu mismatch")
        _require(entry["marker_positions_content_verified"] is (kind == "MARKER_POSITIONS"),
                 "Object Values marker coverage must be explicitly verified")
        timestamp = entry["observed_at"]
        _require(isinstance(timestamp, str), "export timestamp missing")
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid export timestamp") from exc
        _require(dt.tzinfo is not None and dt.utcoffset() is not None,
                 "export timestamp must include timezone")
        source = _local_file(path.parent, entry["file"])
        _require(source not in source_files, "same source file reused for two exports")
        source_files.add(source)
        normalized.append({**entry, "source": source})
    _require(observed == {(p, kind) for p in TARGETS for kind in MENUS},
             "missing FACAD 32F/13F x 3 export combination")
    return data, normalized


def stage(intake_path: Path, output_dir: Path) -> Path:
    """Stage six real files in a PRIVATE, independent root using the canonical LOT08 schema.

    This generates DIRECT_EVIDENCE_PARTIAL only. Numeric parity is NEVER inferred.
    The attestation fields are operator claims, not independently proved GUI actions.
    """
    data, entries = _checked_input(intake_path)
    output = output_dir.resolve()
    _require(not output.is_relative_to(ROOT.resolve()), "private output must be OUTSIDE the Git repository")
    _require(not output.exists(), "private output destination must not already exist")
    _require(output.parent.is_dir() and not output.parent.is_symlink(), "output parent must exist")
    baseline = json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    _require(baseline["status"] == "DIRECT_DEFINITION_OBSERVED"
             and baseline["evidence_records"] == [] and baseline["parity_rows"] == [],
             "canonical source manifest is not pristine; manual reconciliation required")
    _require({p["target_id"] for p in baseline["profiles"]} == set(TARGETS),
             "canonical profiles changed")
    manifest = copy.deepcopy(baseline)
    manifest["status"] = "DIRECT_EVIDENCE_PARTIAL"
    for profile in manifest["profiles"]:
        profile["observation_status"] = "PARTIAL"
    records = []
    with tempfile.TemporaryDirectory(prefix=".facad-private-", dir=output.parent) as temporary:
        private_root = Path(temporary)
        for entry in entries:
            profile, kind = entry["profile_target_id"], entry["artifact_kind"]
            filename = entry["source"].name
            _require(filename not in (".", "..") and "/" not in filename and "\\" not in filename,
                     "invalid vendor filename")
            evidence_rel = PurePosixPath(
                "docs/audits/evidence/facad", TARGETS[profile], kind, filename
            )
            dest = private_root.joinpath(*evidence_rel.parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Vendor bytes remain untouched and private; hash is computed from the COPY.
            shutil.copyfile(entry["source"], dest)
            digest = hashlib.sha256(dest.read_bytes()).hexdigest()
            _require(digest == hashlib.sha256(entry["source"].read_bytes()).hexdigest(),
                     "vendor copy changed; stop")
            records.append({
                "evidence_id": f"ROBERT_{TARGETS[profile]}_{kind}",
                "artifact_kind": kind,
                "profile_target_id": profile,
                "source_path": evidence_rel.as_posix(),
                "source_filename": filename,
                "sha256": digest,
                "facad_version": VERSION,
                "observed_at": entry["observed_at"],
                "same_trace_case_id": data["same_trace_case_id"],
            })
        manifest["evidence_records"] = records
        _require(len(records) == 6 and manifest["parity_rows"] == [],
                 "staged evidence count and parity gate")
        errors = validate_manifest(manifest, private_root)
        _require(not errors, "canonical LOT08 validator rejected staging: " + "; ".join(errors))
        canonical_rel = DEFAULT_MANIFEST.relative_to(ROOT)
        dest_manifest = private_root / canonical_rel
        dest_manifest.parent.mkdir(parents=True, exist_ok=True)
        dest_manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.rename(private_root, output)
    return output / DEFAULT_MANIFEST.relative_to(ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake", type=Path, required=True, help="Private six-file intake JSON")
    parser.add_argument("--private-output", type=Path, required=True, help="Fresh output directory OUTSIDE the repo")
    args = parser.parse_args()
    try:
        path = stage(args.intake, args.private_output)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"FACAD_PRIVATE_STAGING_FAIL_CLOSED={type(exc).__name__}: {exc}")
        return 2
    print("FACAD_PRIVATE_STAGING_STATUS=DIRECT_EVIDENCE_PARTIAL")
    print("FACAD_PRIVATE_STAGING_AUTHENTIC_EXPORTS=6")
    print("FACAD_PRIVATE_STAGING_NUMERIC_PARITY_PROVED=false")
    print("FACAD_PRIVATE_STAGING_CANONICAL_VALIDATOR=PASS")
    print(f"FACAD_PRIVATE_STAGING_MANIFEST={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
