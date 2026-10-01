#!/usr/bin/env python3
"""Aggregate D3 AMMPS batch checkpoints and prove national coverage."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate(batch_dirs: list[Path], expected_total: int, expected_updated_at: str, expected_pages: int):
    page_map: dict[int, dict] = {}
    row_map: dict[str, dict] = {}
    conflicts: list[str] = []
    source_duplicate_pages: list[dict] = []
    source_row_count = 0
    batch_summaries: list[dict] = []

    for d in batch_dirs:
        manifest = load_json(d / "manifest.json")
        rows = load_json(d / "rows.json")
        if manifest["reported_total"] != expected_total:
            raise AssertionError(f"{d}: total drift {manifest['reported_total']} != {expected_total}")
        if manifest["updated_at"] != expected_updated_at:
            raise AssertionError(f"{d}: date drift {manifest['updated_at']} != {expected_updated_at}")
        if manifest.get("mutated_dictionary") is not False:
            raise AssertionError(f"{d}: dictionary mutation flag is not false")

        for p in manifest["pages"]:
            n = int(p["page"])
            if n in page_map:
                raise AssertionError(f"duplicate page checkpoint: {n}")
            page_map[n] = p

            raw_path = d / "raw" / f"page-{n}.html"
            if not raw_path.exists():
                raise AssertionError(f"{d}: missing raw HTML for page {n}")
            raw_html = raw_path.read_text(encoding="utf-8")
            raw_cards = len(BeautifulSoup(raw_html, "html.parser").select(".medicament-card"))
            source_row_count += raw_cards
            parsed_count = int(p["parsed_count"])
            cross_batch_dup = int(p.get("duplicate_ids_within_batch", 0))
            duplicate_count = raw_cards - parsed_count + cross_batch_dup
            if duplicate_count > 0:
                source_duplicate_pages.append({
                    "page": n,
                    "raw_cards": raw_cards,
                    "parsed_count": parsed_count,
                    "duplicate_ids_within_batch": cross_batch_dup,
                    "source_duplicate_count": duplicate_count,
                })

        for row in rows:
            rid = row["regulatory_presentation_id"]
            if rid in row_map:
                a = dict(row_map[rid]); b = dict(row)
                a.pop("source_page_url", None); b.pop("source_page_url", None)
                if a != b:
                    conflicts.append(rid)
            else:
                row_map[rid] = row

        batch_summaries.append({
            "name": d.name,
            "start_page": manifest["start_page"],
            "end_page": manifest["end_page"],
            "page_count": manifest["page_count"],
            "parsed_unique_count": manifest["parsed_unique_count"],
        })

    expected_page_set = set(range(1, expected_pages + 1))
    actual_page_set = set(page_map)
    missing_pages = sorted(expected_page_set - actual_page_set)
    extra_pages = sorted(actual_page_set - expected_page_set)

    result = {
        "schema": "digital-crown-ammps-d3-national-aggregate.1",
        "expected_total": expected_total,
        "updated_at": expected_updated_at,
        "expected_pages": expected_pages,
        "covered_pages": len(actual_page_set),
        "missing_pages": missing_pages,
        "extra_pages": extra_pages,
        "source_row_count": source_row_count,
        "unique_presentations": len(row_map),
        "source_duplicate_count": source_row_count - len(row_map),
        "source_duplicate_pages": sorted(source_duplicate_pages, key=lambda x: x["page"]),
        "conflicting_ids": sorted(set(conflicts)),
        "batch_count": len(batch_dirs),
        "batches": sorted(batch_summaries, key=lambda x: x["start_page"]),
    }
    if missing_pages or extra_pages or conflicts:
        raise AssertionError(json.dumps(result, ensure_ascii=False, indent=2))
    if source_row_count != expected_total:
        raise AssertionError(
            f"source row coverage mismatch: {source_row_count} != {expected_total}"
        )
    if len(row_map) > expected_total:
        raise AssertionError(
            f"unique presentations exceed source rows: {len(row_map)} > {expected_total}"
        )
    return result, sorted(
        row_map.values(),
        key=lambda r: (
            str(r.get("nom") or "").upper(),
            str(r.get("dci") or "").upper(),
            str(r.get("dosage") or "").upper(),
            str(r.get("forme") or "").upper(),
            str(r.get("presentation") or "").upper(),
        ),
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--glob", default="ammps-d3-batch-*")
    p.add_argument("--expected-total", type=int, required=True)
    p.add_argument("--expected-updated-at", required=True)
    p.add_argument("--expected-pages", type=int, required=True)
    p.add_argument("--manifest-out", required=True)
    p.add_argument("--rows-out", required=True)
    args = p.parse_args()

    batch_dirs = sorted(p for p in Path(args.root).glob(args.glob) if p.is_dir())
    if not batch_dirs:
        raise SystemExit("no batch directories found")

    result, rows = aggregate(
        batch_dirs,
        args.expected_total,
        args.expected_updated_at,
        args.expected_pages,
    )
    Path(args.manifest_out).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    Path(args.rows_out).write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
