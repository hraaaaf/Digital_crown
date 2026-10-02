#!/usr/bin/env python3
"""Promote the certified D3 national AMMPS rows through the D2 incremental merge.

No reset, no implicit deletion, no clinical inference.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from merge_ammps_dictionary_incremental import merge_dictionary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--existing", required=True)
    ap.add_argument("--national-rows", required=True)
    ap.add_argument("--updated-at", required=True, help="DD/MM/YYYY")
    ap.add_argument("--out", required=True)
    ap.add_argument("--diff", required=True)
    args = ap.parse_args()

    existing = json.loads(Path(args.existing).read_text(encoding="utf-8"))
    rows = json.loads(Path(args.national_rows).read_text(encoding="utf-8"))
    if not isinstance(existing, list) or not isinstance(rows, list):
        raise TypeError("existing and national rows must be JSON arrays")

    report = {"page_meta": {"updated_at": args.updated_at}, "rows": rows}
    merged, diff = merge_dictionary(existing, [report])

    Path(args.out).write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.diff).write_text(json.dumps(diff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diff, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
