#!/usr/bin/env python3
"""Read-only lexical color-debt inventory, not WCAG or visual certification.

Compare exact historical Wave02 base with the current checkout. Counts are
regex hits in product source, *not* verified eligible migrations: clinical
graphics, brands, overlays, printed material and UI semantics need triage.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import csv
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = "72302ecd6fcddd526a76370ce04af55ff2b41eab"
OUT = ROOT / "artifacts" / "theme-hardcode-audit"
OUT.mkdir(parents=True, exist_ok=True)

BASE_COLORS = r"slate|gray|zinc|neutral|stone"
STATUS_COLORS = r"red|rose|pink|amber|orange|yellow|green|emerald|lime|teal"
BRAND_COLORS = r"blue|sky|cyan|indigo|violet|purple|fuchsia"
UTILITY = r"(?:bg|text|border|ring|shadow|divide|placeholder|fill|stroke|from|via|to)"
PREFIX = r"(?<![\w/-])!?(?:(?:[a-z][\w-]*):)*"
SUFFIX = r"(?:-\d{2,3}(?:/\d{1,3})?|-\d{1,3}/\[\d+(?:\.\d+)?\])"
PATTERNS = {
    "neutral_palette": re.compile(PREFIX + UTILITY + r"-(?:" + BASE_COLORS + r")" + SUFFIX + r"(?![\w/-])"),
    "status_palette": re.compile(PREFIX + UTILITY + r"-(?:" + STATUS_COLORS + r")" + SUFFIX + r"(?![\w/-])"),
    "brand_palette": re.compile(PREFIX + UTILITY + r"-(?:" + BRAND_COLORS + r")" + SUFFIX + r"(?![\w/-])"),
    "white_black": re.compile(PREFIX + UTILITY + r"-(?:white|black)(?:/\d{1,3})?(?![\w/-])"),
    "arbitrary_hex": re.compile(PREFIX + UTILITY + r"-\[(?:#(?:[0-9a-fA-F]{3,8})|(?:rgba?|hsla?)\([^)\n]+\))\]"),
    "inline_hex": re.compile(r"(?<![\w#])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})(?![0-9a-fA-F])"),
    "inline_rgb": re.compile(r"\b(?:rgba?|hsla?)\(\s*(?:\d|#|var\()"),
}
FRONTEND = "frontend/src/"
EXTS = (".tsx", ".ts", ".jsx", ".js")
EXCLUDED = (".test.", ".spec.", ".stories.", ".story.", "/__tests__/", "/__mocks__/", "/mocks/", "/fixtures/", "/__generated__/")


def product_source(path: str) -> bool:
    return path.startswith(FRONTEND) and path.endswith(EXTS) and not any(t in path for t in EXCLUDED)


def tracked(ref: str) -> set[str]:
    listing = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", FRONTEND],
        cwd=ROOT, text=True,
    )
    return {x for x in listing.splitlines() if product_source(x)}


def source(ref: str, path: str) -> str:
    if ref == "HEAD":
        return (ROOT / path).read_text(encoding="utf-8", errors="replace")
    return subprocess.check_output(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT,
    ).decode("utf-8", errors="replace")


def matches(content: str) -> dict[str, list[tuple[int, str]]]:
    rows: dict[str, list[tuple[int, str]]] = {}
    for kind, pattern in PATTERNS.items():
        matches = []
        for hit in pattern.finditer(content):
            line = content.count("\n", 0, hit.start()) + 1
            matches.append((line, hit.group(0)))
        rows[kind] = matches
    return rows


def area(path: str) -> str:
    if path.startswith("frontend/src/pages/"):
        return "Pages"
    if path.startswith("frontend/src/features/"):
        return "Features/" + path.split("/")[3]
    if path.startswith("frontend/src/components/"):
        return "Shared components"
    return "Other source"


def main() -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    historical = tracked(BASE)
    current = tracked("HEAD")
    totals_base, totals_head = Counter(), Counter()
    by_area = {}
    files = []
    for path in sorted(historical | current):
        start = matches(source(BASE, path)) if path in historical else {k: [] for k in PATTERNS}
        final = matches(source("HEAD", path)) if path in current else {k: [] for k in PATTERNS}
        a, b = Counter({k: len(v) for k, v in start.items()}), Counter({k: len(v) for k, v in final.items()})
        totals_base.update(a)
        totals_head.update(b)
        section = area(path)
        if section not in by_area:
            by_area[section] = {"before": Counter(), "after": Counter(), "files_with_hits": 0}
        by_area[section]["before"].update(a)
        by_area[section]["after"].update(b)
        if sum(b.values()):
            by_area[section]["files_with_hits"] += 1
        if sum(a.values()) or sum(b.values()):
            files.append({
                "path": path, "area": section,
                "before": dict(a), "after": dict(b),
                "total_before": sum(a.values()), "total_after": sum(b.values()),
                "delta": sum(b.values()) - sum(a.values()),
                "sample": [
                    {"line": line, "kind": kind, "token": token}
                    for kind in PATTERNS for line, token in final[kind][:2]
                ][:8],
            })
    families = list(PATTERNS)
    result = {
        "head": head, "historical_base": BASE,
        "method": "product frontend/src TS/TSX/JS/JSX regex hits, excluding tests/stories/mocks/fixtures; possible overlap between arbitrary-hex and inline-hex counts; no clinical/brand/UI/overlay qualification; no WCAG certification",
        "files_scanned_before": len(historical), "files_scanned_after": len(current),
        "files_with_candidate_hits": sum(f["total_after"] > 0 for f in files),
        "counts_before": dict(totals_base), "counts_after": dict(totals_head),
        "total_before": sum(totals_base.values()), "total_after": sum(totals_head.values()),
        "total_delta": sum(totals_head.values()) - sum(totals_base.values()),
        "area": {area: {"before": dict(v["before"]), "after": dict(v["after"]),
                        "total_after": sum(v["after"].values()),
                        "files_with_hits": v["files_with_hits"]}
                 for area, v in sorted(by_area.items())},
        "top_25": sorted(files, key=lambda f: (-f["total_after"], f["path"]))[:25],
        "all_affected_files": files,
        "historical_kpi_not_comparable": {"completed_substitutions": 4060, "original_target_estimate": 8813, "ratio": round(4060 / 8813 * 100, 2)},
    }
    (OUT / "report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (OUT / "per-file.csv").open("w", encoding="utf-8", newline="") as handle:
        cols = ["path", "area", "total_before", "total_after", "delta"] + ["after_" + c for c in families]
        writer = csv.DictWriter(handle, fieldnames=cols)
        writer.writeheader()
        for f in files:
            writer.writerow({**{k: f[k] for k in cols[:5]}, **{"after_" + k: f["after"].get(k, 0) for k in families}})
    print("THEME_RESIDUAL_AUDIT_JSON=" + json.dumps({
        k: result[k] for k in ("head", "historical_base", "files_scanned_after",
            "files_with_candidate_hits", "counts_before", "counts_after",
            "total_before", "total_after", "total_delta", "historical_kpi_not_comparable")
    }))
    print("THEME_RESIDUAL_AUDIT_TOP=" + json.dumps([
        {"file": f["path"], "count": f["total_after"], "neutral": f["after"].get("neutral_palette", 0),
         "status": f["after"].get("status_palette", 0), "white_black": f["after"].get("white_black", 0)}
        for f in result["top_25"][:20]
    ]))
    print("THEME_RESIDUAL_AUDIT_AREA=" + json.dumps([
        {"area": name, "count": v["total_after"], "files": v["files_with_hits"]}
        for name, v in sorted(result["area"].items(), key=lambda x: -x[1]["total_after"])[:18]
    ]))
    print("THEME_RESIDUAL_AUDIT_PASS inventory-only, no automatic product changes")


if __name__ == "__main__":
    main()
