#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"
OUT_DIR = ROOT / "artifacts" / "g0-interactive-inventory"
OUT_DIR.mkdir(parents=True, exist_ok=True)

CODE_EXTS = {".tsx", ".ts", ".jsx", ".js"}
EXCLUDED_PARTS = {"node_modules", "dist", "build", "coverage", "__snapshots__", "preview", "test"}
TEST_RE = re.compile(r"(?:\.test|\.spec)\.[jt]sx?$")
ROUTE_RE = re.compile(r'<Route\b[^>]*\bpath\s*=\s*["\']([^"\']+)["\']', re.S)

PATTERNS = {
    "button": re.compile(r"<button\b", re.I),
    "input_button": re.compile(r'<input\b[^>]*\btype\s*=\s*["\'](?:button|submit|reset)["\']', re.I | re.S),
    "select": re.compile(r"<select\b", re.I),
    "textarea": re.compile(r"<textarea\b", re.I),
    "form": re.compile(r"<form\b", re.I),
    "link": re.compile(r"<(?:Link|NavLink)\b"),
    "onclick": re.compile(r"\bonClick\s*="),
    "onchange": re.compile(r"\bonChange\s*="),
    "onsubmit": re.compile(r"\bonSubmit\s*="),
    "role_button": re.compile(r'\brole\s*=\s*["\']button["\']'),
    "dialog_signal": re.compile(r"(?:<CrownDialog\b|<Dialog\b|<Modal\b|\bmodal\b)", re.I),
    "drawer_signal": re.compile(r"(?:<Drawer\b|\bdrawer\b)", re.I),
    "tab_signal": re.compile(r"(?:role\s*=\s*[\"\']tab[\"\']|<Tabs?\b|\bactiveTab\b|\bsetActiveTab\b)", re.I),
    "menu_signal": re.compile(r"(?:<Menu\b|<Dropdown\b|\bmenuOpen\b|\bsetMenuOpen\b)", re.I),
    "navigate_signal": re.compile(r"(?:\bnavigate\s*\(|<Navigate\b)"),
    "mutating_api_signal": re.compile(r"\b(?:api|axios|authService|cabinetApi)\.(?:post|put|patch|delete)\b", re.I),
}

def line_number(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1

def relevant_code_files():
    for path in SRC.rglob("*"):
        if not path.is_file() or path.suffix not in CODE_EXTS:
            continue
        rel = path.relative_to(ROOT)
        if TEST_RE.search(path.name):
            continue
        if set(rel.parts) & EXCLUDED_PARTS:
            continue
        yield path, rel.as_posix()

files = []
routes = []
control_candidates = []
signals_by_file = defaultdict(Counter)

for path, rel in relevant_code_files():
    text = path.read_text(encoding="utf-8", errors="ignore")
    files.append(rel)
    for m in ROUTE_RE.finditer(text):
        routes.append({"path": m.group(1), "file": rel, "line": line_number(text, m.start())})
    for category, regex in PATTERNS.items():
        for m in regex.finditer(text):
            control_candidates.append({
                "category": category,
                "file": rel,
                "line": line_number(text, m.start()),
                "excerpt": text[m.start():m.start()+220].splitlines()[0][:220].strip(),
            })
            signals_by_file[rel][category] += 1

main_path = SRC / "main.tsx"
bootstrap_surfaces = []
if main_path.exists():
    text = main_path.read_text(encoding="utf-8", errors="ignore")
    bootstrap_surfaces = sorted(set(re.findall(r'["\'](/(?:mobile|patient-companion)[^"\']*)["\']', text)))

test_files = [
    p.relative_to(ROOT).as_posix()
    for p in SRC.rglob("*")
    if p.is_file() and TEST_RE.search(p.name)
]

def lot_for_route(route: str) -> str:
    if route.startswith("/mobile") or route in {"/landing", "/download", "/activate", "/login", "/register", "/terms", "/privacy", "/setup"}:
        return "G1"
    if route.startswith("/patients") or route == "/dashboard":
        return "G2"
    if route == "/agenda":
        return "G3"
    if route in {"/accounting", "/analytics", "/bibliotheque", "/science-hub"}:
        return "G4"
    if route == "/settings":
        return "G5"
    if route == "/super-admin":
        return "G6"
    if route.startswith("/stock") or route.startswith("/approvisionnement"):
        return "G7"
    return "G8-review"

route_rows = []
for r in sorted(routes, key=lambda x: (x["path"], x["file"], x["line"])):
    row = dict(r)
    row["lot"] = lot_for_route(r["path"])
    route_rows.append(row)

category_counts = Counter(c["category"] for c in control_candidates)
manifest = {
    "head": "runtime",
    "source_files_scanned": len(files),
    "route_count": len(route_rows),
    "unique_route_count": len({r["path"] for r in route_rows}),
    "bootstrap_surfaces": bootstrap_surfaces,
    "candidate_signal_count": len(control_candidates),
    "category_counts": dict(sorted(category_counts.items())),
    "test_file_count": len(test_files),
    "routes": route_rows,
    "candidate_controls": control_candidates,
    "signals_by_file": {k: dict(v) for k, v in sorted(signals_by_file.items())},
    "test_files": sorted(test_files),
    "limitations": [
        "Static inventory only: candidates need semantic reconciliation before becoming the applicable control denominator.",
        "Signals can overlap; candidate_signal_count is not a coverage denominator.",
        "Runtime/config-generated controls are reconciled during G1-G8 behavior passes.",
    ],
}
(OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

lines = [
    "# Digital Crown — G0 Global Interactive Inventory",
    "",
    "## Machine inventory",
    f"- Source files scanned: **{manifest['source_files_scanned']}**",
    f"- Route declarations found: **{manifest['route_count']}**",
    f"- Unique explicit route paths: **{manifest['unique_route_count']}**",
    f"- Static interactive/action signals: **{manifest['candidate_signal_count']}**",
    f"- Existing test files discovered: **{manifest['test_file_count']}**",
    "",
    "> Static signal count is not the certified denominator. Overlaps and non-user-facing signals require semantic reconciliation.",
    "",
    "## Explicit routes",
    "",
    "| Route | Lot | Source |",
    "|---|---|---|",
]
for r in route_rows:
    lines.append(f"| `{r['path']}` | {r['lot']} | `{r['file']}:{r['line']}` |")
if bootstrap_surfaces:
    lines += ["", "## Bootstrap-only surfaces", ""] + [f"- `{s}`" for s in bootstrap_surfaces]
lines += ["", "## Static signal counts", ""]
for key, value in sorted(category_counts.items()):
    lines.append(f"- {key}: **{value}**")
lines += [
    "",
    "## Reconciliation contract",
    "1. Collapse overlapping signals into one user-visible control row.",
    "2. Record state/context variants: success, refusal/error, loading/disabled, roles/permissions, offline and double-action/non-mutation when relevant.",
    "3. Map behavioral proof or mark GAP.",
    "4. Declare denominator/coverage only after reconciliation.",
    "5. Route GAPs to G1→G8, then G9/G10.",
]
(OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps({
    "source_files_scanned": manifest["source_files_scanned"],
    "unique_route_count": manifest["unique_route_count"],
    "candidate_signal_count": manifest["candidate_signal_count"],
    "test_file_count": manifest["test_file_count"],
}, indent=2))
