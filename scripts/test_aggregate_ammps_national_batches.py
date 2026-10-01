#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("aggregate_ammps_national_batches.py")
spec = importlib.util.spec_from_file_location("aggregate_ammps_national_batches", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

def write_batch(root: Path, name: str, page: int, rid: str):
    d = root / name
    d.mkdir()
    (d / "manifest.json").write_text(json.dumps({
        "reported_total": 2,
        "updated_at": "01/10/2026",
        "mutated_dictionary": False,
        "start_page": page,
        "end_page": page,
        "page_count": 1,
        "parsed_unique_count": 1,
        "pages": [{"page": page, "http_status": 200}],
    }), encoding="utf-8")
    (d / "rows.json").write_text(json.dumps([{
        "regulatory_presentation_id": rid,
        "nom": f"DRUG {page}",
        "source_page_url": f"https://ammps.gov.ma/recherche-medicaments?page={page}",
    }]), encoding="utf-8")
    return d

with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    b1 = write_batch(root, "b1", 1, "ammps-reg:a")
    b2 = write_batch(root, "b2", 2, "ammps-reg:b")
    result, rows = mod.aggregate([b1, b2], 2, "01/10/2026", 2)
    assert result["covered_pages"] == 2
    assert result["unique_presentations"] == 2
    assert result["missing_pages"] == []
    assert len(rows) == 2

    try:
        mod.aggregate([b1], 2, "01/10/2026", 2)
    except AssertionError:
        pass
    else:
        raise AssertionError("missing page must fail")

print({"status": "PASS"})
