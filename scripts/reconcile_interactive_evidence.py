#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
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

test_files = [
    p.relative_to(ROOT).as_posix()
    for p in SRC.rglob("*")
    if p.is_file() and re.search(r"(?:\.test|\.spec)\.[jt]sx?$", p.name)
]
gated_tests = [
    p for p in test_files
    if re.search(r"\.g[1-8]Interactive\.test\.[jt]sx?$", p)
    or "buttonMatrix.test" in p
]

def stem_tokens(path: str) -> set[str]:
    stem = Path(path).stem
    stem = re.sub(r"\.(?:g[1-8]Interactive|buttonMatrix)$", "", stem)
    tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", stem)
    return {t.lower() for t in tokens if len(t) >= 3}

def direct_test_candidates(source_path: str) -> list[str]:
    source_stem = Path(source_path).stem.lower()
    source_tokens = stem_tokens(source_path)
    candidates = []
    for test in gated_tests:
        test_stem = Path(test).stem.lower()
        test_tokens = stem_tokens(test)
        if source_stem in test_stem or (source_tokens and source_tokens <= test_tokens):
            candidates.append(test)
    return sorted(candidates)

rows = []
for source_path, counts in sorted(signals_by_file.items()):
    total = sum(counts.values())
    if total <= 0:
        continue
    direct = direct_test_candidates(source_path)
    doc_ref = source_path in proof_text or f"`{source_path}`" in proof_text
    rows.append({
        "source_file": source_path,
        "static_signals": total,
        "direct_gated_test_count": len(direct),
        "direct_gated_tests": ";".join(direct),
        "canonical_doc_reference": "yes" if doc_ref else "no",
        "inspection_required": "no" if direct or doc_ref else "yes",
    })

rows.sort(key=lambda r: (r["inspection_required"] != "yes", -r["static_signals"], r["source_file"]))
inspection = [r for r in rows if r["inspection_required"] == "yes"]

csv_path = ART / "evidence_reconciliation_seed.csv"
with csv_path.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else [
        "source_file","static_signals","direct_gated_test_count","direct_gated_tests",
        "canonical_doc_reference","inspection_required"
    ])
    writer.writeheader()
    writer.writerows(rows)

summary = [
    "# G0 → G9 Evidence Reconciliation Seed",
    "",
    "This is an **inspection queue**, not the semantic denominator and not a coverage score.",
    "",
    f"- Interactive source files in static inventory: **{len(rows)}**",
    f"- Files with a direct gated-test match or canonical G1→G8 reference: **{len(rows)-len(inspection)}**",
    f"- Files requiring semantic inspection: **{len(inspection)}**",
    "",
    "A file may be listed for inspection even when it is indirectly covered by a parent integration test.",
    "Conversely, a direct filename match does not prove that every control in the file is covered.",
    "G9 must adjudicate these rows semantically before freezing the denominator.",
    "",
    "## Highest-signal inspection queue",
    "",
    "| Static signals | Source file |",
    "|---:|---|",
]
for row in inspection[:100]:
    summary.append(f"| {row['static_signals']} | `{row['source_file']}` |")

(ART / "evidence_reconciliation_seed.md").write_text("\n".join(summary)+"\n", encoding="utf-8")

print(json.dumps({
    "interactive_source_files": len(rows),
    "mapped_or_referenced_files": len(rows)-len(inspection),
    "inspection_required_files": len(inspection),
}, indent=2))
