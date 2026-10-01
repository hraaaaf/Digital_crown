#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("crawl_ammps_catalog_batch.py")
spec = importlib.util.spec_from_file_location("crawl_ammps_catalog_batch", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

assert mod.page_url(1) == "https://ammps.gov.ma/recherche-medicaments?page=1"
assert mod.page_url(123).endswith("page=123")
print({"status": "PASS", "page_url_1": mod.page_url(1), "page_url_123": mod.page_url(123)})
