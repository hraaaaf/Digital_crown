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


def group_after_heading(heading):
    nodes = []
    for sibling in heading.next_siblings:
        if getattr(sibling, "name", None) in {"h1", "h2", "h3", "h4", "h5"}:
            break
        nodes.append(sibling)
    return nodes


def group_text(nodes) -> str:
    bits = []
    for node in nodes:
        if hasattr(node, "get_text"):
            bits.append(node.get_text(" ", strip=True))
        else:
            bits.append(str(node))
    return norm(" ".join(bits))


def extract_label(text: str, label: str) -> str:
    # Capture from this label until the next known label or RCP marker.
    next_labels = [re.escape(x) for x in LABELS if x != label]
    stopper = "|".join(next_labels + [re.escape("Télécharger RCP")])
    m = re.search(
        rf"{re.escape(label)}\s*:?[\s]+(.+?)(?=\s+(?:{stopper})\s*:?[\s]+|$)",
        text,
        flags=re.I,
    )
    return norm(m.group(1)) if m else ""


def presentation_id(row: dict) -> str:
    identity = "|".join(
        norm(str(row.get(k) or "")).upper()
        for k in ("nom", "dci", "dosage", "unite", "forme", "presentation", "epi")
    )
    return "ammps-reg:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def parse_page(html: str, source_url: str) -> tuple[list[dict], dict]:
    soup = BeautifulSoup(html, "html.parser")
    body_text = norm(soup.get_text(" ", strip=True))
    total_m = re.search(r"(\d[\d\s]*)\s+médicament\(s\) trouvé\(s\)", body_text, flags=re.I)
    updated_m = re.search(r"Base de données mise à jour le\s+(\d{2}/\d{2}/\d{4})", body_text, flags=re.I)

    rows: list[dict] = []
    seen: set[str] = set()
    headings = soup.find_all(["h3", "h4", "h5"])
    for heading in headings:
        name = norm(heading.get_text(" ", strip=True))
        if not name:
            continue
        nodes = group_after_heading(heading)
        text = group_text(nodes)
        if "Substance active" not in text or "Présentation" not in text:
            continue

        dci = extract_label(text, "Substance active")
        epi = extract_label(text, "EPI")
        dosage_raw = extract_label(text, "Dosage")
        forme = extract_label(text, "Forme")
        presentation = extract_label(text, "Présentation")
        market_status = extract_label(text, "Statut commercialisation")
        ppv = extract_label(text, "PPV")
        ph = extract_label(text, "PH")

        if not (dci and dosage_raw and forme and presentation):
            continue

        # The AMMPS page renders both summary and expanded content. Keep only
        # the richer/detail occurrence (EPI/status) when duplicates exist.
        dosage, unite = split_dosage(dosage_raw)
        links = []
        for node in nodes:
            if hasattr(node, "find_all"):
                links.extend(node.find_all("a", href=True))
        rcp_link = None
        for link in links:
            if "RCP" in norm(link.get_text(" ", strip=True)).upper():
                rcp_link = official_url(link.get("href"))
                if rcp_link:
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
            "rcp_link_observed": bool("Télécharger RCP" in text or rcp_link),
            "rcp_url": rcp_link,
        }
        row["regulatory_presentation_id"] = presentation_id(row)
        key = row["regulatory_presentation_id"]
        if key not in seen:
            seen.add(key)
            rows.append(row)

    return rows, {
        "reported_total": int(re.sub(r"\s+", "", total_m.group(1))) if total_m else None,
        "updated_at": updated_m.group(1) if updated_m else None,
        "heading_count": len(headings),
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

    response = requests.get(
        SEARCH_URL,
        params={"search": args.query},
        timeout=30,
        headers={"User-Agent": "DigitalCrown-AMMPS-Probe/1.0"},
    )
    response.raise_for_status()
    rows, page_meta = parse_page(response.text, response.url)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    html_path = out.with_suffix(".html")
    html_path.write_text(response.text, encoding="utf-8")

    existing = load_existing()
    existing_by_id = {existing_id(row): row for row in existing}
    exact_existing = [existing_by_id[row["regulatory_presentation_id"]] for row in rows if row["regulatory_presentation_id"] in existing_by_id]
    new_rows = [row for row in rows if row["regulatory_presentation_id"] not in existing_by_id]

    report = {
        "query": args.query,
        "source_url": response.url,
        "source_http_status": response.status_code,
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
