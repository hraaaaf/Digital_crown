"""Read-only verification of historical FACAD editor UIA roster ZIP evidence.

Does not install, start, control, or license FACAD; does not copy patient or
vendor export files, and never promotes editor definitions to numeric parity.
Historical ZIPs are operator-provided locally; never uploaded to public CI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile, BadZipFile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/audits/schemas/ortho_lot08_facad_ricketts_editor_uia_45_roster_v1.json"
MAX_ARCHIVE = 12_000_000
MAX_MEMBER = 2_000_000
UI_HEADER = "ControlType.DataGrid|"
CELL_PREFIX = "ControlType.Text|"
DATA_PREFIX = "ControlType.DataItem|"


def require(condition: bool, explanation: str) -> None:
    if not condition:
        raise ValueError(explanation)


def parse_editor(text: str, expected_profile: str) -> tuple[list[dict], int]:
    """Read ONLY the FIRST UIA measurement DataGrid. Heading rows not factors."""
    require("ControlType.Window|Edit Cephalometric Analysis|" in text,
            "not the named FACAD cephalometric analysis editor")
    require(f"ControlType.Edit|{expected_profile}|AUTOID=" in text,
            "historical FACAD profile identity mismatched")
    lines = text.splitlines()
    begin = next((i for i, line in enumerate(lines) if line.startswith(UI_HEADER)), None)
    require(begin is not None, "measurement DataGrid missing")
    rows: list[tuple[str, list[str]]] = []
    for line in lines[begin + 1:]:
        if line.startswith(UI_HEADER):
            break
        if line.startswith(DATA_PREFIX):
            rows.append((line[len(DATA_PREFIX):].split("|", 1)[0], []))
        elif rows and line.startswith(CELL_PREFIX):
            rows[-1][1].append(line[len(CELL_PREFIX):].split("|", 1)[0])
    require(rows, "no measurement rows")
    factors = []
    heading_count = 0
    for name, cells in rows:
        require(len(cells) >= 9 and cells[0] == name and cells[1] != "",
                "malformed measurement table cells")
        if cells[1] == "Heading":
            heading_count += 1
            continue
        require(re.fullmatch(r"[A-Za-z0-9(). /'-]{1,80}", name) is not None,
                "unexpected factor label encoding")
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9]{1,32}", cells[1]) is not None,
                "invalid calculation-type cell")
        factors.append({"order": len(factors) + 1, "facad_label": name})
    require(len({r["facad_label"] for r in factors}) == len(factors),
            "duplicate factor names")
    return factors, heading_count


def verify_archive(zip_path: Path, profile: dict) -> dict:
    path = zip_path.resolve(strict=True)
    require(path.is_file() and 0 < path.stat().st_size <= MAX_ARCHIVE,
            "archived evidence missing, oversized or not a regular file")
    actual_zip_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    require(actual_zip_sha == profile["source_artifact_zip_sha256"],
            "historic ZIP SHA256 mismatch")
    member = profile["source_uia_member_name"]
    require(re.fullmatch(r"d1c-Ricketts__(?:32|13)_F_-measurements-ui\.txt", member)
            is not None, "unexpected UIA archive member")
    try:
        with ZipFile(path, "r") as z:
            members = z.infolist()
            require(len({x.filename for x in members}) == len(members),
                    "archive contains duplicate members")
            matches = [x for x in members if x.filename == member]
            require(len(matches) == 1 and 0 < matches[0].file_size <= MAX_MEMBER,
                    "UIA member missing, ambiguous or oversized")
            raw = z.read(matches[0])
    except (BadZipFile, RuntimeError, OSError) as exc:
        raise ValueError("invalid or unreadable historic ZIP") from exc
    require(len(raw) == profile["source_uia_member_byte_count"],
            "archived UIA member byte count mismatch")
    require(hashlib.sha256(raw).hexdigest() == profile["source_uia_member_sha256"],
            "UIA member SHA256 mismatch")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid UTF-8 in historic UIA capture") from exc
    expected = "Ricketts (32 F)" if profile["profile_target_id"].endswith("32F_COMPATIBILITY_TARGET") else "Ricketts (13 F)"
    rows, headings = parse_editor(text, expected)
    require(rows == profile["ordered_factor_labels"],
            "historical GUI factor name/order differs from versioned roster")
    require(len(rows) == profile["observed_factor_count"] and
            headings == (6 if expected == "Ricketts (32 F)" else 4),
            "historical UIA row/heading counts differ from source evidence")
    return {
        "profile_target_id": profile["profile_target_id"],
        "artifact_id": profile["source_artifact_id"],
        "vendor_gui_definitions_verified": len(rows),
        "section_headings": headings,
        "zip_sha256_match": True,
        "uia_sha256_match": True,
        "exact_45_label_order_match": True,
        "numeric_parity_verified": False,
    }


def verify_pair(roster: dict, sources: dict[str, Path]) -> dict:
    require(roster["schema_version"] == "ORTHO_LOT08_FACAD_RICKETTS_EDITOR_UIA_45_ROSTER_V1"
            and roster["status"] == "HISTORICAL_EDITOR_DEFINITION_UIA_OBSERVED_ONLY"
            and roster["scientific_authority"] is False and roster["compatibility_only"] is True
            and roster["safety_rules"]["no_automatic_numeric_parity"] is True,
            "historical source-lock guard")
    profiles = roster["profile_rosters"]
    require(len(profiles) == 2, "two historical profiles required")
    required = {p["profile_target_id"] for p in profiles}
    require(len(required) == 2 and set(sources) == required, "historical profile pairing mismatch")
    checked = [verify_archive(sources[p["profile_target_id"]], p) for p in profiles]
    require(sorted(r["vendor_gui_definitions_verified"] for r in checked) == [13, 32],
            "expected 13 and 32 editor factors")
    return {
        "status": "HISTORICAL_GUI_DEFINITION_ARCHIVES_INDEPENDENTLY_VERIFIED",
        "records": checked,
        "total_ordered_factor_definitions": 45,
        "authentic_vendor_numeric_exports_checked": 0,
        "numeric_parity_observed": 0,
        "clinical_no_go": True,
        "warning": "Historical definition rows are not real FACAD numeric results.",
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ricketts32f-zip", required=True, type=Path)
    p.add_argument("--ricketts13f-zip", required=True, type=Path)
    p.add_argument("--roster", type=Path, default=SCHEMA)
    args = p.parse_args()
    try:
        require(args.roster.resolve() == SCHEMA.resolve(), "only canonical historical roster accepted")
        roster = json.loads(SCHEMA.read_text(encoding="utf-8"))
        result = verify_pair(roster, {
            "FACAD_RICKETTS_32F_COMPATIBILITY_TARGET": args.ricketts32f_zip,
            "FACAD_RICKETTS_13F_COMPATIBILITY_TARGET": args.ricketts13f_zip,
        })
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"FACAD_HISTORIC_ROSTER_FAIL_CLOSED={type(exc).__name__}: {exc}")
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
