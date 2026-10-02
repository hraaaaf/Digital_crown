#!/usr/bin/env python3
"""Controlled national AMMPS catalogue batch crawler.

D3 goals:
- fetch an explicit inclusive page range only;
- preserve raw HTML + parsed rows + manifest;
- require stable total/update metadata across the batch;
- de-duplicate with the same regulatory identity as D1/D2;
- never mutate the canonical dictionary.

This script is tooling only; runtime remains offline.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

from probe_ammps_dictionary_sync import SEARCH_URL, parse_page

UA = "DigitalCrown-AMMPS-D3/1.0"


def page_url(page: int) -> str:
    return SEARCH_URL + "?" + urlencode({"page": page})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--start-page", type=int, required=True)
    p.add_argument("--end-page", type=int, required=True)
    p.add_argument("--delay-seconds", type=float, default=0.35)
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()

    if args.start_page < 1 or args.end_page < args.start_page:
        raise SystemExit("invalid page range")
    if args.delay_seconds < 0:
        raise SystemExit("delay must be >= 0")

    root = Path(args.out_dir)
    raw_dir = root / "raw"
    root.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    by_id: dict[str, dict] = {}
    pages: list[dict] = []
    reported_total = None
    updated_at = None

    for page in range(args.start_page, args.end_page + 1):
        url = page_url(page)
        r = requests.get(url, timeout=30, headers={"User-Agent": UA})
        r.raise_for_status()
        (raw_dir / f"page-{page}.html").write_text(r.text, encoding="utf-8")

        rows, meta = parse_page(r.text, r.url)
        if not rows:
            raise RuntimeError(f"page {page}: zero rows parsed")

        current_total = meta.get("reported_total")
        current_updated = meta.get("updated_at")
        if current_total is None or current_updated is None:
            raise RuntimeError(f"page {page}: missing total/update metadata")

        if reported_total is None:
            reported_total = current_total
            updated_at = current_updated
        elif current_total != reported_total or current_updated != updated_at:
            raise RuntimeError(
                f"metadata drift within batch at page {page}: "
                f"{current_total}/{current_updated} != {reported_total}/{updated_at}"
            )

        duplicate_ids = 0
        for row in rows:
            rid = row["regulatory_presentation_id"]
            if rid in by_id:
                duplicate_ids += 1
                if by_id[rid] != row:
                    # source URL naturally differs only if the same package is duplicated
                    a = dict(by_id[rid]); b = dict(row)
                    a.pop("source_page_url", None); b.pop("source_page_url", None)
                    if a != b:
                        raise RuntimeError(f"conflicting duplicate identity {rid}")
            else:
                by_id[rid] = row

        pages.append({
            "page": page,
            "url": r.url,
            "http_status": r.status_code,
            "parsed_count": len(rows),
            "duplicate_ids_within_batch": duplicate_ids,
        })
        if page != args.end_page and args.delay_seconds:
            time.sleep(args.delay_seconds)

    rows = sorted(
        by_id.values(),
        key=lambda x: (
            str(x.get("nom") or "").upper(),
            str(x.get("dci") or "").upper(),
            str(x.get("dosage") or "").upper(),
            str(x.get("forme") or "").upper(),
            str(x.get("presentation") or "").upper(),
        ),
    )
    (root / "rows.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema": "digital-crown-ammps-d3-batch.1",
        "start_page": args.start_page,
        "end_page": args.end_page,
        "page_count": args.end_page - args.start_page + 1,
        "reported_total": reported_total,
        "updated_at": updated_at,
        "parsed_unique_count": len(rows),
        "pages": pages,
        "mutated_dictionary": False,
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
