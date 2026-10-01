#!/usr/bin/env python3
"""Inspect AMMPS RCP controls for one exact presentation.

Read-only diagnostic tool. It does not download RCP content, mutate the
dictionary, or extract clinical fields.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from probe_ammps_dictionary_sync import norm, presentation_id

SEARCH_URL = "https://ammps.gov.ma/recherche-medicaments"


def inspect(html: str, source_url: str, wanted_id: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {
        "source_url": source_url,
        "presentation_id": wanted_id,
        "matched": False,
        "controls": [],
        "scripts": [],
    }

    for card in soup.select(".medicament-card"):
        title = card.select_one(".medicament-title")
        if not title:
            continue
        target = norm(card.get("data-bs-target"))
        modal = soup.select_one(target) if target.startswith("#") else None
        if modal is None:
            continue

        fields = {}
        for item in modal.select(".ammps-modal-item"):
            label = item.select_one(".ammps-modal-label")
            value = item.select_one(".ammps-modal-value")
            if label and value:
                fields[norm(label.get_text(" ", strip=True))] = norm(value.get_text(" ", strip=True))

        dosage_raw = fields.get("Dosage", "")
        m = re.match(r"^(.+?)\s+((?:MG|G|MCG|µG|UG|UI|MBQ)(?:\s*/\s*.+)?)$", dosage_raw, flags=re.I)
        if m:
            dosage, unite = norm(m.group(1)), norm(m.group(2)).upper().replace("UG", "µG")
        else:
            dosage, unite = norm(dosage_raw), ""

        row = {
            "nom": norm(title.get_text(" ", strip=True)),
            "dci": fields.get("Substance active", ""),
            "dosage": dosage,
            "unite": unite,
            "forme": fields.get("Forme", ""),
            "presentation": fields.get("Présentation", ""),
            "epi": fields.get("EPI", ""),
        }
        rid = presentation_id(row)
        if rid != wanted_id:
            continue

        result["matched"] = True
        result["row"] = row
        for el in modal.find_all(["a", "button"]):
            text = norm(el.get_text(" ", strip=True))
            attrs = {str(k): str(v) for k, v in el.attrs.items()}
            hay = (text + " " + " ".join(f"{k}={v}" for k, v in attrs.items())).upper()
            if "RCP" in hay or "PDF" in hay or "DOWNLOAD" in hay:
                result["controls"].append({
                    "tag": el.name,
                    "text": text,
                    "attrs": attrs,
                    "html": str(el)[:4000],
                    "parent_html": str(el.parent)[:8000] if el.parent else None,
                })
        break

    patterns = re.compile(r"(RCP|\.PDF\b|DOWNLOAD|FETCH\(|AJAX|XMLHTTPREQUEST)", re.I)
    for i, script in enumerate(soup.find_all("script")):
        content = script.string or script.get_text("\n", strip=False) or ""
        if patterns.search(content):
            result["scripts"].append({
                "index": i,
                "src": script.get("src"),
                "snippet": content[:12000],
            })

    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", default="AMOXICILLINE")
    ap.add_argument("--presentation-id", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    r = requests.get(
        SEARCH_URL,
        params={"search": args.query},
        timeout=30,
        headers={"User-Agent": "DigitalCrown-AMMPS-D4-Inspector/1.0"},
    )
    r.raise_for_status()
    result = inspect(r.text, r.url, args.presentation_id)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "matched": result["matched"],
        "control_count": len(result["controls"]),
        "script_hits": len(result["scripts"]),
        "source_url": result["source_url"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["matched"] and result["controls"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
