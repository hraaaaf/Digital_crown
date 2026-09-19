#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "g0-interactive-inventory"
MANIFEST = ART / "manifest.json"
AUDIT_DIR = ROOT / "docs" / "clinic" / "audits"
SRC = ROOT / "frontend" / "src"

if not MANIFEST.exists():
    raise SystemExit("Run scripts/inventory_interactive_controls.py first.")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
signals_by_file: dict[str, dict[str, int]] = manifest["signals_by_file"]

proof_docs = []
for gate in range(1, 9):
    path = AUDIT_DIR / f"V1_07_GLOBAL_INTERACTIVE_AUDIT_G{gate}.md"
    if path.exists():
        proof_docs.append(path.read_text(encoding="utf-8", errors="ignore"))
proof_text = "\n".join(proof_docs)

test_paths = [
    p
    for p in SRC.rglob("*")
    if p.is_file() and re.search(r"(?:\.test|\.spec)\.[jt]sx?$", p.name)
]
gated_test_paths = [
    p
    for p in test_paths
    if re.search(r"\.g[1-8]Interactive\.test\.[jt]sx?$", p.name)
    or "buttonMatrix.test" in p.name
]
gated_tests = [p.relative_to(ROOT).as_posix() for p in gated_test_paths]
test_text = {
    p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8", errors="ignore")
    for p in gated_test_paths
}

IMPORT_RE = re.compile(r"(?:from\s+|import\s*\()\s*['\"]([^'\"]+)['\"]")
SOURCE_EXTENSIONS = (".ts", ".tsx", ".js", ".jsx")


def stem_tokens(path: str) -> set[str]:
    stem = Path(path).stem
    tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", stem)
    return {t.lower() for t in tokens if len(t) >= 3}


def heuristic_test_candidates(source_path: str) -> list[str]:
    """Filename/token hints only. Never sufficient to remove inspection requirement."""
    source_stem = Path(source_path).stem.lower()
    source_tokens = stem_tokens(source_path)
    candidates = []
    for test in gated_tests:
        test_stem = Path(test).stem.lower()
        test_tokens = stem_tokens(test)
        if source_stem in test_stem or (source_tokens and source_tokens <= test_tokens):
            candidates.append(test)
    return sorted(candidates)


def resolved_import_candidates(test_abs: Path, specifier: str) -> set[Path]:
    if specifier.startswith("./") or specifier.startswith("../"):
        raw = (test_abs.parent / specifier).resolve()
    elif specifier.startswith("@/"):
        raw = (SRC / specifier[2:]).resolve()
    else:
        return set()

    candidates = {raw}
    if raw.suffix not in SOURCE_EXTENSIONS:
        candidates.update(Path(str(raw) + ext) for ext in SOURCE_EXTENSIONS)
        candidates.update(raw / f"index{ext}" for ext in SOURCE_EXTENSIONS)
    return {p.resolve() for p in candidates}


def direct_import_candidates(source_path: str) -> list[str]:
    """Tests that import this exact source path through a relative or @/ import."""
    source_abs = (ROOT / source_path).resolve()
    candidates: list[str] = []
    for test_rel in gated_tests:
        test_abs = ROOT / test_rel
        for specifier in IMPORT_RE.findall(test_text[test_rel]):
            if source_abs in resolved_import_candidates(test_abs, specifier):
                candidates.append(test_rel)
                break
    return sorted(candidates)


rows = []
for source_path, counts in sorted(signals_by_file.items()):
    total = sum(counts.values())
    if total <= 0:
        continue
    direct = direct_import_candidates(source_path)
    heuristic = heuristic_test_candidates(source_path)
    doc_ref = source_path in proof_text or f"`{source_path}`" in proof_text
    rows.append({
        "source_file": source_path,
        "static_signals": total,
        "direct_import_test_count": len(direct),
        "direct_import_tests": ";".join(direct),
        "heuristic_test_count": len(heuristic),
        "heuristic_tests": ";".join(heuristic),
        "canonical_doc_reference": "yes" if doc_ref else "no",
        "inspection_required": "no" if direct or doc_ref else "yes",
    })

rows.sort(key=lambda r: (r["inspection_required"] != "yes", -r["static_signals"], r["source_file"]))
inspection = [r for r in rows if r["inspection_required"] == "yes"]

csv_path = ART / "evidence_reconciliation_seed.csv"
with csv_path.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(
        fh,
        fieldnames=list(rows[0].keys()) if rows else [
            "source_file",
            "static_signals",
            "direct_import_test_count",
            "direct_import_tests",
            "heuristic_test_count",
            "heuristic_tests",
            "canonical_doc_reference",
            "inspection_required",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

summary = [
    "# G0 → G9 Evidence Reconciliation Seed",
    "",
    "This is an **inspection queue**, not the semantic denominator and not a coverage score.",
    "",
    f"- Interactive source files in static inventory: **{len(rows)}**",
    f"- Files with a direct-import gated test or canonical G1→G8 reference: **{len(rows)-len(inspection)}**",
    f"- Files requiring semantic inspection: **{len(inspection)}**",
    "",
    "Only an exact source import or an explicit canonical audit reference removes a file from the priority inspection queue.",
    "Filename/token matches are retained as hints only and never count as proof.",
    "A file may still be listed for inspection even when it is indirectly covered by a parent integration test.",
    "Conversely, a direct import or canonical reference does not prove that every control in the file is covered.",
    "G9 must adjudicate the full set semantically before freezing the denominator.",
    "",
    "## Highest-signal inspection queue",
    "",
    "| Static signals | Source file | Heuristic test hints |",
    "|---:|---|---:|",
]
for row in inspection[:100]:
    summary.append(
        f"| {row['static_signals']} | `{row['source_file']}` | {row['heuristic_test_count']} |"
    )

(ART / "evidence_reconciliation_seed.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

print(json.dumps({
    "interactive_source_files": len(rows),
    "mapped_or_referenced_files": len(rows) - len(inspection),
    "inspection_required_files": len(inspection),
}, indent=2))
