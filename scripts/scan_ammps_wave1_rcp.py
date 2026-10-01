#!/usr/bin/env python3
"""Scan AMMPS Wave-1 queries for enabled RCP controls.

Read-only. No document download, no clinical extraction, no dictionary mutation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from probe_ammps_dictionary_sync import norm, presentation_id, split_dosage

SEARCH_URL = "https://ammps.gov.ma/recherche-medicaments"


def scan_query(query: str, max_pages: int = 100) -> dict:
    session = requests.Session()
    headers = {"User-Agent": "DigitalCrown-AMMPS-D4-RCPScan/1.0"}
    presentations = []
    enabled = []
    disabled = []
    pages = 0

    for page in range(1, max_pages + 1):
        r = session.get(
            SEARCH_URL,
            params={"search": query, "page": page},
            timeout=30,
            headers=headers,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".medicament-card")
        if not cards:
            break
        pages += 1

        for card in cards:
            title = card.select_one(".medicament-title")
            target = norm(card.get("data-bs-target"))
            modal = soup.select_one(target) if target.startswith("#") else None
            if not title or modal is None:
                continue
            fields = {}
            for item in modal.select(".ammps-modal-item"):
                label = item.select_one(".ammps-modal-label")
                value = item.select_one(".ammps-modal-value")
                if label and value:
                    fields[norm(label.get_text(" ", strip=True))] = norm(value.get_text(" ", strip=True))

            dosage, unite = split_dosage(fields.get("Dosage", ""))
            row = {
                "nom": norm(title.get_text(" ", strip=True)),
                "dci": fields.get("Substance active", ""),
                "dosage": dosage,
                "unite": unite,
                "forme": fields.get("Forme", ""),
                "presentation": fields.get("Présentation", ""),
                "epi": fields.get("EPI", ""),
            }
            if not all(row.get(k) for k in ("nom", "dci", "dosage", "forme", "presentation")):
                continue
            rid = presentation_id(row)
            rcp = None
            for el in modal.find_all(["a", "button"]):
                text = norm(el.get_text(" ", strip=True))
                attrs = {str(k): str(v) for k, v in el.attrs.items()}
                hay = (text + " " + " ".join(f"{k}={v}" for k, v in attrs.items())).upper()
                if "RCP" not in hay:
                    continue
                href = norm(el.get("href"))
                is_disabled = (
                    el.get("aria-disabled") == "true"
                    or "disabled" in " ".join(el.get("class", [])).lower()
                    or href.lower() in {"", "#", "javascript:void(0)"}
                )
                rcp = {
                    "tag": el.name,
                    "text": text,
                    "href": href or None,
                    "attrs": attrs,
                    "enabled": not is_disabled,
                }
                break

            item = {**row, "regulatory_presentation_id": rid, "page": page, "rcp_control": rcp}
            presentations.append(item)
            if rcp:
                (enabled if rcp["enabled"] else disabled).append(item)

    return {
        "query": query,
        "pages_checked": pages,
        "presentation_count": len(presentations),
        "rcp_control_count": len(enabled) + len(disabled),
        "enabled_rcp_count": len(enabled),
        "disabled_rcp_count": len(disabled),
        "enabled": enabled,
        "disabled_examples": disabled[:5],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = {
        "source": SEARCH_URL,
        "queries": [scan_query(q) for q in args.queries],
        "mutated_dictionary": False,
        "downloaded_rcp": False,
        "extracted_clinical_fields": False,
    }
    result["enabled_total"] = sum(q["enabled_rcp_count"] for q in result["queries"])
    result["disabled_total"] = sum(q["disabled_rcp_count"] for q in result["queries"])

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "enabled_total": result["enabled_total"],
        "disabled_total": result["disabled_total"],
        "queries": [
            {
                "query": q["query"],
                "presentations": q["presentation_count"],
                "enabled": q["enabled_rcp_count"],
                "disabled": q["disabled_rcp_count"],
            }
            for q in result["queries"]
        ],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
