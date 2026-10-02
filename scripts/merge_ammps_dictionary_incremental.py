#!/usr/bin/env python3
"""Deterministic incremental merge for the Morocco medication dictionary.

Rules:
- Existing dictionary is the authority for fields not supplied by a newer AMMPS observation.
- Incoming AMMPS observations can add presentations or refresh regulatory/catalog fields.
- No implicit deletion.
- No clinical inference.
- RCP state is fail-closed: an observed placeholder never erases an existing verified RCP URL/hash.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

IDENTITY_FIELDS = ("nom", "dci", "dosage", "unite", "forme", "presentation", "epi")
REFRESHABLE_FIELDS = (
    "nom", "dci", "dosage", "unite", "forme", "presentation", "epi",
    "market_status", "ppv", "ph", "source_page_url",
)
PRESERVED_FIELDS = (
    "amm_status", "rcp_snapshot_status", "rcp_sha256", "rcp_checked_at",
)


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def presentation_id(row: dict[str, Any]) -> str:
    existing = norm(row.get("regulatory_presentation_id"))
    if existing:
        return existing
    identity = "|".join(norm(row.get(k)).upper() for k in IDENTITY_FIELDS)
    return "ammps-reg:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def iso_date(ddmmyyyy: str | None) -> str | None:
    if not ddmmyyyy:
        return None
    try:
        return datetime.strptime(ddmmyyyy, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def normalize_existing(row: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(row)
    out["regulatory_presentation_id"] = presentation_id(out)
    return out


def new_entry(incoming: dict[str, Any], observed_date: str | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for field in REFRESHABLE_FIELDS:
        if field in incoming:
            out[field] = copy.deepcopy(incoming[field])
    out["regulatory_presentation_id"] = presentation_id(incoming)
    out["amm_status"] = "PENDING_VERIFICATION"
    out["market_status_checked_at"] = observed_date
    out["source_snapshot_date"] = observed_date
    out["rcp_link_observed"] = bool(incoming.get("rcp_link_observed"))
    out["rcp_url"] = incoming.get("rcp_url") or None
    out["rcp_snapshot_status"] = "PENDING_DOWNLOAD"
    out["rcp_sha256"] = None
    out["rcp_checked_at"] = None
    return out


def refresh_existing(existing: dict[str, Any], incoming: dict[str, Any], observed_date: str | None) -> tuple[dict[str, Any], list[str]]:
    out = normalize_existing(existing)
    changed: list[str] = []

    for field in REFRESHABLE_FIELDS:
        if field not in incoming:
            continue
        value = copy.deepcopy(incoming[field])
        if out.get(field) != value:
            out[field] = value
            changed.append(field)

    # Provenance dates move only when the source gives a valid snapshot date.
    if observed_date:
        for field in ("market_status_checked_at", "source_snapshot_date"):
            if out.get(field) != observed_date:
                out[field] = observed_date
                changed.append(field)

    observed = bool(incoming.get("rcp_link_observed"))
    if observed and not bool(out.get("rcp_link_observed")):
        out["rcp_link_observed"] = True
        changed.append("rcp_link_observed")

    # Never erase a verified/previous RCP URL because the current page exposes
    # only a JS placeholder. Accept a new URL only when the incoming probe has one.
    incoming_rcp = incoming.get("rcp_url") or None
    if incoming_rcp and out.get("rcp_url") != incoming_rcp:
        out["rcp_url"] = incoming_rcp
        if not out.get("rcp_snapshot_status"):
            out["rcp_snapshot_status"] = "PENDING_DOWNLOAD"
        changed.append("rcp_url")

    for field in PRESERVED_FIELDS:
        if field in existing and field not in out:
            out[field] = copy.deepcopy(existing[field])

    return out, changed


def merge_dictionary(existing_rows: list[dict[str, Any]], reports: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    existing = [normalize_existing(row) for row in existing_rows]
    by_id = {row["regulatory_presentation_id"]: row for row in existing}

    if len(by_id) != len(existing):
        raise ValueError("Existing dictionary contains duplicate regulatory presentation identities")

    added: list[str] = []
    updated: dict[str, list[str]] = {}
    incoming_seen: set[str] = set()
    source_snapshots: set[str] = set()

    for report in reports:
        meta = report.get("page_meta") or {}
        observed_date = iso_date(meta.get("updated_at"))
        if observed_date:
            source_snapshots.add(observed_date)
        for incoming in report.get("rows") or []:
            rid = presentation_id(incoming)
            if rid in incoming_seen:
                # Overlapping queries may return the same package. They must not
                # create duplicates; first equivalent observation is sufficient.
                continue
            incoming_seen.add(rid)
            if rid in by_id:
                merged, fields = refresh_existing(by_id[rid], incoming, observed_date)
                by_id[rid] = merged
                if fields:
                    updated[rid] = fields
            else:
                by_id[rid] = new_entry(incoming, observed_date)
                added.append(rid)

    existing_ids = {row["regulatory_presentation_id"] for row in existing}
    final_ids = set(by_id)
    deleted = sorted(existing_ids - final_ids)
    if deleted:
        raise AssertionError(f"Implicit deletion forbidden: {deleted}")

    final = sorted(
        by_id.values(),
        key=lambda r: tuple(norm(r.get(k)).upper() for k in IDENTITY_FIELDS),
    )

    diff = {
        "existing_count": len(existing),
        "incoming_unique_count": len(incoming_seen),
        "final_count": len(final),
        "added_count": len(added),
        "updated_count": len(updated),
        "unchanged_existing_count": len(existing_ids) - len(updated),
        "deleted_count": 0,
        "added_ids": sorted(added),
        "updated": {k: sorted(v) for k, v in sorted(updated.items())},
        "source_snapshot_dates": sorted(source_snapshots),
    }
    return final, diff


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--existing", required=True)
    parser.add_argument("--report", action="append", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--diff", required=True)
    args = parser.parse_args()

    existing = load_json(Path(args.existing))
    reports = [load_json(Path(p)) for p in args.report]
    if not isinstance(existing, list):
        raise TypeError("Existing dictionary must be a JSON array")

    merged, diff = merge_dictionary(existing, reports)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.diff).write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diff, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
