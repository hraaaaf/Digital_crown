#!/usr/bin/env python3
"""Pilot AMMPS medication dictionary probe.

Read-only network probe. It never mutates runtime files.
Purpose:
- fetch the official AMMPS medication search page for a query;
- parse package-level presentations;
- discover official RCP links when exposed;
- compare parsed presentations with the existing incremental dictionary;
- optionally probe one RCP transport without extracting clinical content.

Clinical fields are deliberately NOT inferred here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CURRENT_PATH = ROOT / "backend" / "data" / "medications_ma_ammps_current_2026.json"
BASE_URL = "https://ammps.gov.ma"
SEARCH_URL = BASE_URL + "/recherche-medicaments"
OFFICIAL_HOSTS = {"ammps.gov.ma", "www.ammps.gov.ma"}

LABELS = (
    "Substance active",
    "EPI",
    "Dosage",
    "Forme",
    "Présentation",
    "Statut commercialisation",
    "PPV",
    "PH",
)


def norm(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def split_dosage(value: str) -> tuple[str, str]:
    value = norm(value)
    m = re.match(r"^(.+?)\s+((?:MG|G|MCG|µG|UG|UI|MBQ)(?:\s*/\s*.+)?)$", value, flags=re.I)
    if not m:
        return value, ""
    return norm(m.group(1)), norm(m.group(2)).upper().replace("UG", "µG")


def official_url(value: str | None) -> str | None:
    if not value:
        return None
    absolute = urljoin(BASE_URL, value.strip())
    p = urlparse(absolute)
    if p.scheme != "https" or p.hostname not in OFFICIAL_HOSTS:
        return None
    return absolute


def presentation_id(row: dict) -> str:
    identity = "|".join(
        norm(str(row.get(k) or "")).upper()
        for k in ("nom", "dci", "dosage", "unite", "forme", "presentation", "epi")
    )
    return "ammps-reg:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def _modal_fields(modal) -> dict[str, str]:
    fields: dict[str, str] = {}
    if modal is None:
        return fields
    for item in modal.select(".ammps-modal-item"):
        label = item.select_one(".ammps-modal-label")
        value = item.select_one(".ammps-modal-value")
        if not label or not value:
            continue
        fields[norm(label.get_text(" ", strip=True))] = norm(value.get_text(" ", strip=True))
    return fields


def _next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    link = soup.select_one('a.page-link[rel="next"]')
    if not link:
        return None
    return official_url(link.get("href"))


def parse_page(html: str, source_url: str) -> tuple[list[dict], dict]:
    soup = BeautifulSoup(html, "html.parser")
    body_text = norm(soup.get_text(" ", strip=True))
    total_m = re.search(r"(\d+(?:[ \u00A0\u202F]\d{3})*)\s+médicament\(s\) trouvé\(s\)", body_text, flags=re.I)
    updated_m = re.search(r"Base de données mise à jour le\s+(\d{2}/\d{2}/\d{4})", body_text, flags=re.I)

    rows: list[dict] = []
    seen: set[str] = set()
    for card in soup.select(".medicament-card"):
        title = card.select_one(".medicament-title")
        if not title:
            continue
        name = norm(title.get_text(" ", strip=True))
        target = norm(card.get("data-bs-target"))
        modal = soup.select_one(target) if target.startswith("#") else None
        fields = _modal_fields(modal)

        dci = fields.get("Substance active", "")
        epi = fields.get("EPI", "")
        dosage_raw = fields.get("Dosage", "")
        forme = fields.get("Forme", "")
        presentation = fields.get("Présentation", "")
        market_status = fields.get("Statut commercialisation", "")
        ppv = fields.get("PPV", "")
        ph = fields.get("PH", "")
        if not (name and dci and dosage_raw and forme and presentation):
            continue

        dosage, unite = split_dosage(dosage_raw)
        rcp_url = None
        rcp_link_observed = False
        if modal is not None:
            for link in modal.select("a"):
                if "RCP" not in norm(link.get_text(" ", strip=True)).upper():
                    continue
                rcp_link_observed = True
                href = norm(link.get("href"))
                if href and href.lower() not in {"javascript:void(0)", "#"} and link.get("aria-disabled") != "true":
                    rcp_url = official_url(href)
                    if rcp_url:
                        break

        row = {
            "nom": name,
            "dci": dci,
            "dosage": dosage,
            "unite": unite,
            "forme": forme,
            "presentation": presentation,
            "epi": epi,
            "market_status": market_status,
            "ppv": ppv,
            "ph": ph,
            "source_page_url": source_url,
            "rcp_link_observed": rcp_link_observed,
            "rcp_url": rcp_url,
        }
        row["regulatory_presentation_id"] = presentation_id(row)
        key = row["regulatory_presentation_id"]
        if key not in seen:
            seen.add(key)
            rows.append(row)

    return rows, {
        "reported_total": int(re.sub(r"\s+", "", total_m.group(1))) if total_m else None,
        "updated_at": updated_m.group(1) if updated_m else None,
        "card_count": len(soup.select(".medicament-card")),
        "next_page_url": _next_page_url(soup, source_url),
    }


def fetch_query_pages(query: str, raw_dir: Path) -> tuple[list[dict], dict]:
    all_rows: list[dict] = []
    seen_ids: set[str] = set()
    page_url = SEARCH_URL
    params = {"search": query}
    page_no = 1
    first_meta: dict = {}
    visited: set[str] = set()

    while page_url:
        response = requests.get(
            page_url,
            params=params,
            timeout=30,
            headers={"User-Agent": "DigitalCrown-AMMPS-Probe/1.0"},
        )
        response.raise_for_status()
        params = None
        canonical_url = response.url
        if canonical_url in visited:
            raise RuntimeError(f"Pagination loop detected at {canonical_url}")
        visited.add(canonical_url)

        raw_path = raw_dir / f"page-{page_no}.html"
        raw_path.write_text(response.text, encoding="utf-8")
        rows, meta = parse_page(response.text, canonical_url)
        if page_no == 1:
            first_meta = dict(meta)
        for row in rows:
            rid = row["regulatory_presentation_id"]
            if rid not in seen_ids:
                seen_ids.add(rid)
                all_rows.append(row)
        page_url = meta.get("next_page_url")
        page_no += 1

    return all_rows, {
        "reported_total": first_meta.get("reported_total"),
        "updated_at": first_meta.get("updated_at"),
        "pages_fetched": page_no - 1,
        "parsed_unique": len(all_rows),
    }


def load_existing() -> list[dict]:
    if not CURRENT_PATH.exists():
        return []
    raw = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else []


def existing_id(row: dict) -> str:
    if row.get("regulatory_presentation_id"):
        return str(row["regulatory_presentation_id"])
    return presentation_id(row)


def probe_rcp(url: str | None) -> dict:
    if not url:
        return {"status": "NO_URL"}
    try:
        r = requests.get(url, timeout=30, allow_redirects=True, headers={"User-Agent": "DigitalCrown-AMMPS-Probe/1.0"})
        ctype = r.headers.get("content-type", "")
        return {
            "status": "FETCHED" if r.ok else "HTTP_ERROR",
            "http_status": r.status_code,
            "final_url": r.url,
            "content_type": ctype,
            "size_bytes": len(r.content),
            "pdf_signature": r.content.startswith(b"%PDF-"),
            "sha256": hashlib.sha256(r.content).hexdigest() if r.ok and r.content else None,
        }
    except Exception as exc:
        return {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="DOLIPRANE")
    parser.add_argument("--out", required=True)
    parser.add_argument("--probe-one-rcp", action="store_true")
    args = parser.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = out.parent / (out.stem + "-raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    rows, page_meta = fetch_query_pages(args.query, raw_dir)

    existing = load_existing()
    existing_by_id = {existing_id(row): row for row in existing}
    exact_existing = [existing_by_id[row["regulatory_presentation_id"]] for row in rows if row["regulatory_presentation_id"] in existing_by_id]
    new_rows = [row for row in rows if row["regulatory_presentation_id"] not in existing_by_id]

    report = {
        "query": args.query,
        "source_url": SEARCH_URL,
        "source_http_status": 200,
        "page_meta": page_meta,
        "existing_dictionary_count": len(existing),
        "parsed_count": len(rows),
        "already_present_count": len(exact_existing),
        "new_count": len(new_rows),
        "rows": rows,
        "rcp_probe": None,
        "mutated_dictionary": False,
    }

    if args.probe_one_rcp:
        first = next((row for row in rows if row.get("rcp_url")), None)
        report["rcp_probe"] = {
            "presentation_id": first.get("regulatory_presentation_id") if first else None,
            "nom": first.get("nom") if first else None,
            **probe_rcp(first.get("rcp_url") if first else None),
        }

    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "query": args.query,
        "reported_total": page_meta["reported_total"],
        "updated_at": page_meta["updated_at"],
        "parsed_count": len(rows),
        "already_present_count": len(exact_existing),
        "new_count": len(new_rows),
        "rcp_probe": report["rcp_probe"],
    }, ensure_ascii=False, indent=2))
    if not rows:
        print("ERROR: no medication presentations parsed", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
